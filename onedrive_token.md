按以下步骤一步步来配置 Azure 应用注册，以便 ComfyUI 的 OneDrive 节点可以成功认证并上传文件。

---

## ✅ 目标

配置一个 Azure AD 应用注册，使其支持 **设备代码流（Device Code Flow）**，并授予 **读写 OneDrive 文件** 的权限。

---

## 🧭 步骤概览

1. 登录 Azure 门户
2. 创建新应用注册
3. 配置应用权限
4. 启用公共客户端流
5. 获取 `client_id`
6. 在 ComfyUI 中使用

---

## 🔧 步骤 1：登录 Azure 门户

打开浏览器，访问：

🔗 [https://portal.azure.com/](https://portal.azure.com/)

使用你的微软账户登录（可以是个人账户，如 outlook.com，也可以是组织账户）

---

## 🔧 步骤 2：创建新应用注册

1. 左侧菜单搜索并点击 **Azure Active Directory**
2. 点击左侧菜单中的 **应用注册 (App registrations)**
3. 点击顶部的 **+ 新注册 (+ New registration)**

### 📝 填写应用信息：

- **名称 (Name)**：随便起一个名字，比如 `ComfyUI OneDrive Uploader`
- **受支持的账户类型 (Supported account types)**：
  - ✅ 选择：**任何组织目录(任何 Azure AD 目录 - 多租户)和个人 Microsoft 账户**  
    （即：`Accounts in any organizational directory ... and personal Microsoft accounts`）
- **重定向 URI (Redirect URI)**：
  - 平台选择：**Web**
  - URI 填写：`https://login.microsoftonline.com/common/oauth2/nativeclient`
  - （这个是设备代码流必须的）

✅ 点击 **注册 (Register)**

---

## 🔧 步骤 3：获取 `client_id`

注册成功后，你会进入应用的概览页面。

复制以下信息备用：

- **应用程序（客户端）ID (Application (client) ID)**  
  👉 这就是你要填入 `config.json` 的 `client_id`

---

## 🔧 步骤 4：配置 API 权限

1. 在左侧菜单中点击 **API 权限 (API permissions)**
2. 点击 **+ 添加权限 (+ Add a permission)**
3. 选择 **Microsoft Graph**
4. 选择 **委托的权限 (Delegated permissions)**
5. 搜索并勾选以下权限：
   - ✅ `Files.ReadWrite.All`（读写用户所有文件）
   - ✅ `offline_access`（可选，用于获取刷新令牌）
6. 点击 **添加权限 (Add permissions)**

### ⚠️ 重要：授予权限

- 如果你是个人账户，点击 **“代表组织授予管理员同意”(Grant admin consent for ...)**（虽然你是个人账户，但 Azure 会允许）
- 如果是组织账户，需要联系管理员授予权限

---

## 🔧 步骤 5：启用公共客户端流

1. 在左侧菜单中点击 **清单 (Manifest)**
2. 找到 `"allowPublicClient": false`，改为：

```json
"allowPublicClient": true
```

3. 点击顶部的 **保存 (Save)**

✅ 这一步非常重要！设备代码流需要启用公共客户端。

---

## 🔧 步骤 6：在 ComfyUI 中配置

打开你的 ComfyUI OneDrive 节点目录下的 `config.json` 文件（如果不存在，请创建）：

```json
{
  "client_id": "你复制的 Application (client) ID",
  "client_secret": ""
}
```

> ⚠️ 注意：设备代码流 **不需要填写 `client_secret`**，留空即可！

---

## 🔧 步骤 7：重启 ComfyUI 并测试

1. 重启 ComfyUI
2. 打开 OneDrive 节点，点击认证按钮
3. 查看控制台输出，应该会显示：

```
To sign in, use a web browser to open the page https://www.microsoft.com/link and enter the code XXXXXXX to authenticate.
```

4. 打开链接并输入代码，完成授权

---

## ✅ 完成！

你现在已经成功配置了 Azure 应用注册，OneDrive 节点应该可以正常上传文件了！

---

## 🧪 附加建议

- 如果你是组织账户（如学校/公司邮箱），请确认管理员允许你注册应用并授予权限
- 如果你只想访问自己的 OneDrive，可以考虑使用 **个人微软账户**（如 outlook.com）
- 如果你希望支持自动刷新令牌，可以启用 `offline_access` 权限

---

## ✅ 获取 `bot_token` 和 `chat_id`

### 1. 创建 Telegram Bot

- 在 Telegram 中搜索 `@BotFather`
- 发送 `/start`
- 发送 `/newbot`
- 按提示输入 Bot 名称 和 用户名（必须以 `bot` 结尾，如 `MyComfyUIBot`）
- BotFather 会返回一个 **API Token**，复制它填入 `bot_token`

### 2. 获取 `chat_id`

#### 方法一：群组/频道

- 将你的 Bot 添加为群组管理员（或频道管理员）
- 发送任意消息到群组
- 访问以下链接（替换 `YOUR_BOT_TOKEN`）：

```
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

- 查看返回的 JSON，找到 `"chat":{"id": -1001234567890}`，复制这个负数 ID

> 注意：频道或超级群组的 ID 是负数，且以 `-100` 开头

#### 方法二：私聊

- 在 Telegram 中私聊你的 Bot
- 发一条消息（如 "hi"）
- 访问上面的 `getUpdates` 链接
- 找到 `"chat":{"id": 123456789}`，复制这个正数 ID

---

## ✅ 第六步：重启 ComfyUI

```bash
python main.py
```

在节点菜单中搜索：

> **📤 Post Image to Telegram**

拖入工作流，连接图像输出，填写标题（支持 emoji 😊），运行即可！

---

## 🎉 功能亮点

- ✅ 自动保存本地 + UI 预览（和 SaveImage 一致）
- ✅ 发送到 Telegram 群组/频道/私聊
- ✅ 支持自定义标题文本
- ✅ 配置分离，安全不泄露 token
- ✅ 认证失败时自动降级为本地预览，不中断流程
- ✅ 日志清晰，便于调试

---

## 🚀 可选增强功能（后续可加）

- 支持发送多图（Media Group）
- 支持异步发送（不阻塞工作流）
- 支持变量替换（如 `{seed}`, `{model}`）
- 支持自动压缩/缩放大图
- 支持代理（如在国内使用）

---

需要我帮你写一个 **自动获取 chat_id 的脚本**，或者 **支持变量替换的增强版**？随时告诉我！

现在就去试试吧 —— 你的 AI 作品可以一键飞到 Telegram 群里惊艳所有人了！ 🚀🖼️

