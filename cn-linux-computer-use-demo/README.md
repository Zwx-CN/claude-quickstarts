# 国产模型 Linux Computer Use Demo

这是一个薄层 Computer Use harness 原型，目标是先跑通：

```text
Linux desktop screenshot -> Qwen 3.7 Plus -> structured action -> pyautogui/X11 -> trace
```

它不是 OSWorld 的完整 benchmark runtime。它借鉴 OSWorld 已验证的几件事：

- 截图作为主要 observation。
- 坐标使用 `[0, 1000]` 归一化空间。
- 模型输出 `<tool_call>...</tool_call>`。
- parser 将 tool call 转为受控动作。
- 每一步保存 screenshot、model response、actions trace。

## 技术栈

```text
Debian container
Xvfb + Openbox
x11vnc + noVNC + websockify
FastAPI
pyautogui + mss
Qwen 3.7 Plus via OpenAI-compatible API
JSONL trace
```

## 快速开始

```bash
cp .env.example .env
# 编辑 .env，填入 QWEN_API_KEY / QWEN_BASE_URL / QWEN_MODEL
scripts/deploy.sh
```

打开：

- API: `http://localhost:8000/health`
- noVNC: `http://localhost:6080/vnc.html`

提交任务：

```bash
curl -X POST http://localhost:8000/tasks \
  -H 'content-type: application/json' \
  -d '{"instruction":"Open a text editor and type hello from Qwen.","max_steps":10}'
```

查询任务：

```bash
curl http://localhost:8000/tasks/<task-id>
```

轨迹会写到：

```text
experiments/traces/<task-id>/
  events.jsonl
  screenshots/
```

## API

- `GET /health`
- `GET /screenshot`
- `POST /actions`
- `POST /tasks`
- `GET /tasks/{task_id}`

## Provider 与部署

这个 demo 把 provider 拆成三层，避免把模型和运行环境绑死：

- `CU_MODEL_PROVIDER`: 模型 API 与 action 解析族，例如 `qwen`。
- `CU_DESKTOP_PROVIDER`: Linux 桌面实际跑在哪里，例如 `docker` / `utm`。
- `CU_DEPLOY_PROFILE`: 这套东西怎么部署，例如 `local-docker` / `local-utm`。

默认在 `.env` 里配置：

```bash
CU_MODEL_PROVIDER=qwen
CU_DESKTOP_PROVIDER=docker
CU_DEPLOY_PROFILE=local-docker
```

可选值：

| Profile | 用途 | 入口 |
|-|-|-|
| `local-docker` | 本机 Docker/Colima/Docker Desktop 直接跑容器，最接近云端 pod 形态。 | `scripts/deploy.sh local-docker` |
| `local-utm` | 先在 UTM 里开一个可见 Linux VM，再在 VM 里跑 Docker Compose。适合肉眼看完整 VM 桌面。 | `scripts/deploy.sh local-utm` |

### local-docker

```bash
scripts/deploy.sh local-docker
```

打开：

- API: `http://localhost:8000/health`
- noVNC: `http://localhost:6080/vnc.html`

### local-utm

UTM 这条路径的原则是：Mac 负责同步代码和发启动命令，demo 真正运行在 UTM 里的 Ubuntu VM。

一次性准备 VM：

```bash
# 在 Ubuntu VM 里执行，先让 Mac 能 SSH 进来
sudo apt-get update
sudo apt-get install -y openssh-server rsync
sudo systemctl enable --now ssh
hostname -I
```

从 Mac 把 demo 同步进 VM：

```bash
scripts/sync_to_vm.sh --target ubuntu@<utm-vm-ip>
```

然后在 Ubuntu VM 里安装 Docker：

```bash
cd ~/cn-linux-computer-use-demo
bash scripts/provision_ubuntu_vm.sh
```

重新登录一次 VM，让当前用户获得 Docker 权限。

之后从 Mac 同步 `.env` 并启动：

```bash
scripts/sync_to_vm.sh --target ubuntu@<utm-vm-ip> --with-env --start
```

`--with-env` 会把本机 `.env` 同步到 VM。只对你信任的 VM 使用它；同步后脚本会在 VM 上执行 `chmod 600 .env`。

启动时脚本会优先使用 `docker compose`，如果 VM 里只有 Debian 打包的 Compose v1，则自动改用 `docker-compose`。

如果 Docker Hub 或镜像源不稳定，也可以直接在 VM 的可见 X11 桌面上运行 API。这个模式不会启动容器，`pyautogui` 会操作你在 UTM 窗口里看到的桌面：

```bash
# 在 VM 里执行
cd ~/cn-linux-computer-use-demo
bash scripts/provision_direct_vm.sh
scripts/run_visible_vm_api.sh
```

直跑模式下可以在 VM 里访问：

- API: `http://localhost:8000/health`
- 截图: `http://localhost:8000/screenshot`

打开：

- API: `http://<utm-vm-ip>:8000/health`
- noVNC: `http://<utm-vm-ip>:6080/vnc.html`

这一步只启动本地 API 和桌面容器，不会调用模型。真正调用模型的是 `POST /tasks`。

`POST /actions` 接受内部动作格式，例如：

```json
{
  "kind": "left_click",
  "coordinate": { "x": 500, "y": 500, "space": "normalized" }
}
```

## 模型输出格式

Qwen adapter 会要求模型输出一条 OSWorld 风格 action：

```text
Action: click the editor
<tool_call>{"name":"computer","arguments":{"action":"left_click","coordinate":[512,420]}}</tool_call>
```

也兼容 Qwen XML 风格：

```text
<tool_call>
<function=computer_use>
<parameter=action>key</parameter>
<parameter=keys>["ctrl", "s"]</parameter>
</function>
</tool_call>
```

第一版不会执行模型返回的任意 `pyautogui` Python 代码，只执行结构化动作。

## 后续路线

1. 接入真实 Qwen 3.7 Plus API，校准 model name、headers 和图像输入格式。
2. 从 OSWorld 的 Qwen adapter 补强 prompt、history pruning 和失败重试。
3. 增加 `KimiAdapter`、`MiniMaxM3Adapter`、`GLM5VAdapter`。
4. 增加 OSWorld 风格 `tasks/<name>/setup.py + verify.py`。
5. 把 `PyAutoGUIX11Backend` 抽象旁路成 `CUABackend` / `WaylandBackend`。
