# 部署指南（让 demo 变成「可点链接」）

本项目（以及 `doc_qa_project`、`leave_agent`）都是 Streamlit 应用。两种上线方式：

---

## 方式一：HuggingFace Spaces（免费、免信用卡，推荐）

最适合学生/求职 demo，几分钟得到公开链接，**不需要 Docker**。

1. 打开 https://huggingface.co/spaces → 点 **Create new Space**
2. 填名字（如 `leave-agent-langchain`），**SDK 选 `Streamlit`**，Visibility 选 **Public**
3. 把本目录的 `app.py` 和 `requirements.txt` 上传（或 `git push` 到 Space 的 git 仓库）
4. 进入 Space 的 **Settings → Secrets**，添加：
   - Name: `DEEPSEEK_API_KEY`
   - Value: 你的 `sk-...`
5. 等待构建完成，Space 会给你一个 `https://<用户名>-<空间名>.hf.space` 的公开链接，别人点开就能用。

> 注意：不要上传 `.env` 文件，密钥只放 Secrets。本仓库的 `.gitignore` 已排除 `.env`。

---

## 方式二：云服务器 / 任意支持 Docker 的平台

适合想要长期稳定、或公司内网部署。

### 1) 本地先验证镜像
```bash
docker build -t langchain-agent .
docker run -e DEEPSEEK_API_KEY=sk-xxx -p 8503:8503 langchain-agent
# 浏览器打开 http://localhost:8503
```

### 2) 用 docker-compose（推荐）
先在当前目录建一个 `.env`（只放密钥，别提交）：
```
DEEPSEEK_API_KEY=sk-xxx
```
然后：
```bash
docker compose up -d --build
```

### 3) 部署到服务器
把整个目录 `scp`/git 到服务器，安装好 Docker 后同样 `docker compose up -d --build`，
再用 Nginx/Caddy 反代 `localhost:8503` 并配置 HTTPS 域名即可对外访问。

---

## 端口约定（避免三个项目冲突）
- `doc_qa_project` → 8501
- `leave_agent`   → 8502
- `langchain_agent` → 8503
