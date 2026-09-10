---
tags: [embodied-ai, engineering, safety]
type: knowledge
status: published
updated: 2026-09-10
---

# 硬件、实时与安全

> **一句话**：模型给你能力，硬件与安全层给你「能进现场」的资格——延迟预算、算力预算、传感冗余、力与速度限制、急停回路，这五项决定机器人是产品还是展品。
> **难度**： 进阶
> **标签**：`#embodied-ai` `#engineering` `#safety`

## 先看结论

- **延迟预算是硬约束，必须写成数字**：`相机曝光 → 感知 → 策略 → 控制 → 电机响应` 端到端预算（接触类任务常要求 <50–100ms 反馈环），拆开分配到每一段，超预算就往下推或换更小模型。
- **算力决定架构，不是喜好**：板载（Jetson Orin 级、消费级 GPU、NPU）能放得下多大的 VLM，直接决定你是「本地全栈」还是「本地快策略 + 云端慢思考」。
- **实时控制必须在实时线程**：策略推理可以抖（有动作块兜着），底层伺服不能抖。跑 Linux 要做 PREEMPT_RT / 隔离 CPU / 关频率调节，控制总线用 EtherCAT 一类确定性链路。
- **安全是分层冗余，不是单层正确**：硬件急停（Category 0/1）、力矩与速度限幅、安全控制器/监控单元、软件安全层（速度-分离监控 SSL）、工作空间围栏——任何一层失效时，另一层还能停。
- **传感冗余不是奢侈品**：纯视觉没有直接力反馈，纯编码器不知道物体是否真被抓起。急停按钮、接触检测、状态灯、声音告警都是「运维能不能信你」的一部分。

## ⏱ 延迟预算示例（50Hz 闭环、夹爪柔顺抓取）

| 阶段 | 预算 | 实现 | 超支后果 |
|---|---|---|---|
| 相机曝光 + 传输 | 10–20ms | 硬触发、GMSL/USB3 驱动直连、避免 ISP 长管线 | 观测滞后，抓移动物失败 |
| 感知/编码 | 5–25ms | 量化视觉塔、缓存特征、多相机共享骨干 | 帧率下降 → 抖动 |
| 慢系统（VLM 意图） | 100–200ms | 异步、5–10Hz、结果给快系统 | 不阻塞控制，但意图过期 |
| 快系统（动作专家） | 3–15ms | 小模型 + 少量去噪步 + 图优化 | 动作块断流 → 空转或跳变 |
| 控制层（IK/阻抗） | 0.2–1ms | 实时线程、预计算、无动态内存分配 | 关节抖、超调 |
| 总线 + 驱动器 | 0.5–2ms | EtherCAT DC 同步、看门狗 | 掉帧 → 突然停或突然动 |
| 机械响应 | 5–20ms | 力矩带宽、减速度能力 | 实际轨迹与命令不符 |

> 💡 **提示**：这张表要贴在项目看板上。「我们把模型从 7B 换成 3B 让 TTFT 从 260ms 降到 90ms」这种话，在有预算表的项目里是例行公事，在没有的项目里是玄学争论。

## 算力形态与部署模式

| 模式 | 延迟 | 断网可用 | 适合 |
|---|---|---|---|
| 全部板载（小 VLM + 小策略） | 最稳（无网络抖动） | ✅ | 高动态、安全敏感、量产产品 |
| 板载快策略 + 云端慢系统 | 慢系统 100–400ms，靠动作块兜 | ⚠ 降级：本地缓存技能继续执行 | 需要强语义的场景（家庭、零售） |
| 全部云端（边缘服务器池） | 局域网 5–30ms | ❌ | 固定工位、多台机器人共享算力 |
| 端侧 + 基站双活 | 低 | ✅ | 医疗/工业等不允许断的场合 |

**板载常见配置**（量级参考，具体看代际）：NVIDIA Jetson Orin 系列（数瓦到数十瓦，INT8/FP16 推理）、消费级移动 GPU、NPU/加速器。工程要点是**功耗-散热-算力**三角：持续推理下会热降频，热降频后控制频率掉，机器人行为就变了——必须在高温工况下重测端到端延迟与成功率。

## 安全层：怎么落到代码与硬件

```python
# 软件安全层（放在模型输出与机器人驱动之间，独立于策略进程）
class SafetyMonitor:
    def __init__(self, robot, spec):
        self.r, self.s = robot, spec
        self.last = None
    def check(self, cmd, state, dt):
        # 1) 幅度与速率
        if (d := (cmd.pos - state.tcp_pos)).norm() > self.s.max_step_m:
            return reject("step_too_large", scale_to(d, self.s.max_step_m))
        if (v := (cmd.pos - self.last.pos).norm()/dt) > self.s.max_tcp_vel:
            return reject("vel_limit", clamp_vel(cmd, self.s.max_tcp_vel))
        # 2) 力/功率（与 ISO/TS 15066 的功率与力限制 PFL 对应）
        if state.ext_wrench.norm() > self.s.force_n and not cmd.is_contact_phase:
            return stop(category=1)             # 受控停止，保留动力
        # 3) 人机距离（速度-分离监控 SSL）
        if (p := self.human_nearest_point()) and p.dist < self.s.min_sep(p.human_vel):
            return slow_down_or_stop(p)
        # 4) 关节软限位与自碰撞
        if any(state.joint_pos > self.s.soft_limits):
            return reject("soft_limit", project_inward(cmd))
        if self.s.collides(cmd):
            return reject("self_collision")
        self.last = cmd
        return accept(cmd)
```

**硬件与流程**

- **急停**：物理按钮（Category 0 立即断动力 / Category 1 受控停止后断），必须走安全回路（安全 PLC/双通道），不走软件；操作者可及 + 远程可断
- **看门狗**：控制指令丢失 → 立刻停止（总线 watchdog + 软件心跳）
- **状态可预测**：故障后进入「已知安全态」（放下负载、收臂、断电抱闸），别停在半空托着东西
- **协作机器人限速/限力**：接触力与压强按人机协作标准核算（如 ISO/TS 15066 的 PFL、ISO 10218 的机器人类安全要求），并留验证记录
- **上线前 checklist**：急停响应时间实测、最大接触力实测、断网/断电/断传感器三种注入测试、人员在场时的速度上限、维护后标定复核

## 传感器套件

| 传感 | 提供什么 | 常见坑 |
|---|---|---|
| RGB / RGB-D | 场景几何与语义 | 反光与透明物体失效；深度与彩色时间戳不同步 |
|  wrist 相机 | 精细操作 | 线缆干涉、视野被夹爪挡 |
| 编码器 / IMU | 本体状态与姿态 | 零位漂移、冲击后偏置；需与动力学估计融合 |
| 六维力/力矩 | 接触与插入力 | 标定与重力补偿没做好 → 读数全错 |
| 电流/力矩残差 | 便宜的碰撞检测 | 摩擦模型老化后误报增加 |
| 触觉阵列 | 滑移、边缘、法向力 | 磨损、清洗、跨机标定为难题 |
| UWB / 激光雷达 / 视觉里程计 | 定位与地图 | 人形动态下退化，需与 IMU 紧耦合 |
| 外部安全激光扫描仪 | 人员接近检测 | 覆盖区域与盲区的现场评估 |

## 常见误区

- ❌ 把安全逻辑写进策略训练奖励里：奖励不是保证；「训练时见过碰撞惩罚」不等于「部署时不会撞」
- ❌ 用 WiFi 传控制/急停：抖动与断连不可预测，安全信号必须走有线/专用安全链路
- ❌ 忽略热降频与功耗：室温下测的 200Hz 控制，工作 1 小时后掉到 120Hz，行为就变了
- ❌ 不做「传感器失效注入」：拔掉深度相机、遮住腕相机、IMU 漂 5°，看系统是否安全地停下来——这是验收必测项
- ❌ 以为「模型输出前 clamp 一下就安全」：clamp 在策略进程内，进程崩了就没了；安全层要在独立进程/独立控制器
- ❌ 数据与隐私：现场视频（人脸、文件、工艺）要有分级留存与脱敏，见 [数据与隐私](../10-evaluation-safety/data-privacy.md)

## 小练习

给你的机器人写一份「一页安全验收表」，每项都要有实测数字：急停响应时间、最大允许接触力（含测量方法）、TCP 速度上限、策略崩溃后行为、断网降级行为、控制频率 vs 温度曲线。任何一项写不出来，就是现场会出事的那一项。

## 相关资源

- [ROS 2 实时与控制](https://control.ros.org/)、[EtherCAT](https://www.ethercat.org/)、[Linux PREEMPT_RT](https://wiki.linuxfoundation.org/realtime/start)
- 安全标准入口：[ISO 10218（工业机器人安全）](https://www.iso.org/)、[ISO/TS 15066（协作机器人）](https://www.iso.org/standard/65457.html)
- 算力与部署：[推理经济学与部署形态](../16-ai-infrastructure/inference-economics-deployment.md)

## 相关知识点

- [动作表示与分层控制](action-representation-control.md)
- [评估与基准](evaluation-benchmarks.md)
- [把 Agent 接进机器人](agent-to-robot-bridge.md)
- [沙箱与执行环境](../16-ai-infrastructure/sandbox-execution-environments.md)
