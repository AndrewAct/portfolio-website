# Docker Build Troubleshooting Guide

## 如果遇到 "ERROR: [internal] load metadata" 错误

### 解决方案 1: 先手动拉取基础镜像

```bash
# 在构建之前，先手动拉取基础镜像
docker pull python:3.11.9-alpine

# 然后再构建
docker build -t portfolio-backend .
```

### 解决方案 2: 使用 BuildKit（推荐）

```bash
# 启用 BuildKit
export DOCKER_BUILDKIT=1

# 然后构建
docker build -t portfolio-backend .
```

或者在构建时使用：

```bash
DOCKER_BUILDKIT=1 docker build -t portfolio-backend .
```

### 解决方案 3: 配置 Docker 镜像源（如果在中国大陆）

如果您在中国大陆，访问 Docker Hub 可能较慢，可以配置镜像源：

1. **macOS (Docker Desktop)**:
   - 打开 Docker Desktop
   - 进入 Settings > Docker Engine
   - 添加以下配置：
   
```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false
}
```

2. **Linux**:
   - 编辑 `/etc/docker/daemon.json`:
   
```bash
sudo vim /etc/docker/daemon.json
```

   添加相同的配置，然后重启 Docker：
   
```bash
sudo systemctl restart docker
```

### 解决方案 4: 使用代理（如果可访问）

如果有代理可用：

```bash
# 配置 HTTP/HTTPS 代理
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

# 然后构建
docker build -t portfolio-backend .
```

### 解决方案 5: 清理 Docker 缓存后重试

```bash
# 清理构建缓存
docker builder prune -f

# 清理未使用的镜像
docker image prune -a -f

# 然后重新构建
docker build --no-cache -t portfolio-backend .
```

### 解决方案 6: 检查网络连接

```bash
# 测试 Docker Hub 连接
curl -I https://registry-1.docker.io/

# 测试 DNS 解析
nslookup registry-1.docker.io
```

### 解决方案 7: 使用备用镜像源

如果上述方法都不行，可以尝试使用阿里云或其他云服务商的镜像仓库。

## 快速诊断命令

```bash
# 检查 Docker 是否运行
docker info

# 检查网络连接
docker pull python:3.11.9-alpine

# 查看 Docker 日志（macOS）
tail -f ~/Library/Containers/com.docker.docker/Data/log/vm/dockerd.log

# 查看 Docker 日志（Linux）
sudo journalctl -u docker.service -f
```

## 推荐的最佳实践

1. **始终先拉取基础镜像**：
   ```bash
   docker pull python:3.11.9-alpine
   ```

2. **使用 BuildKit**：
   ```bash
   export DOCKER_BUILDKIT=1
   ```

3. **如果经常构建失败，考虑配置镜像源或代理**

4. **定期清理未使用的资源**：
   ```bash
   docker system prune -a
   ```

