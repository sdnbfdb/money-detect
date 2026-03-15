# D3.js 离线使用配置说明

## ✅ 已完成的修改

### 1. D3.js 本地文件下载
- 已将 D3.js v7.0 库下载到 `qian/d3.v7.min.js` (273KB)
- 文件大小：273.2 KB
- 版本：D3.js v7

### 2. HTML 文件引用方式修改

#### filter.html 和 detal.html 都已修改为：
```javascript
// 动态加载脚本，优先使用本地文件
const script = document.createElement('script');
script.src = 'd3.v7.min.js';
script.onerror = function() {
    console.log('本地 D3.js 加载失败，使用 CDN...');
    const cdnScript = document.createElement('script');
    cdnScript.src = 'https://d3js.org/d3.v7.min.js';
    document.head.appendChild(cdnScript);
};
document.head.appendChild(script);
```

### 3. 加载策略
- **优先使用本地文件**：`d3.v7.min.js`
- **自动回退到 CDN**：如果本地文件不存在或加载失败，自动从 `https://d3js.org/d3.v7.min.js` 加载
- **无需手动切换**：系统会自动选择可用的加载方式

## 🧪 测试方法

### 方法 1：直接访问测试页面
1. 启动 HTTP 服务器（已在 8080 端口运行）：
   ```bash
   python -m http.server 8080
   ```

2. 在浏览器中打开：
   ```
   http://localhost:8080/qian/test_d3.html
   ```

3. 查看结果：
   - ✅ 绿色提示"D3.js 加载成功"并显示柱状图 → 本地文件加载成功
   - ⚠️ 如果能正常显示但控制台显示使用了 CDN → 本地文件未找到，自动切换到 CDN

### 方法 2：测试主页面
1. 访问：`http://localhost:8080/qian/filter.html`
2. 打开浏览器开发者工具（F12）
3. 查看 Console 标签：
   - 如果没有报错，且能看到图谱 → ✅ 成功
   - 如果显示"本地 D3.js 加载失败，使用 CDN..." → 说明本地文件路径有问题

### 方法 3：断网测试
1. 断开网络连接
2. 访问：`http://localhost:8080/qian/filter.html`
3. 如果图谱能正常显示 → ✅ 本地加载成功
4. 如果图谱无法显示 → ❌ 本地文件未正确加载

## 📁 文件结构

```
票务资金展示/
├── qian/
│   ├── d3.v7.min.js          # ← D3.js 本地文件（新增）
│   ├── filter.html           # ← 已修改为支持本地 + CDN
│   ├── detal.html            # ← 已修改为支持本地 + CDN
│   ├── index.html            # （可选修改）
│   └── test_d3.html          # ← 测试页面（新增）
├── hou/
│   └── app.py                # Flask 后端
└── cases/                    # 案件数据文件夹
```

## 🔧 故障排查

### 问题 1：浏览器显示跨域错误
**现象**：Console 显示 `Failed to load resource: net::ERR_FAILED`

**原因**：直接双击打开 HTML 文件（file:// 协议）会导致跨域限制

**解决方案**：
- ✅ 使用 HTTP 服务器访问（推荐）
  ```bash
  cd "c:\Users\sanjin\Desktop\票务资金展示"
  python -m http.server 8080
  ```
- 然后访问：`http://localhost:8080/qian/filter.html`

### 问题 2：本地文件找不到
**现象**：Console 显示"本地 D3.js 加载失败，使用 CDN..."

**检查步骤**：
1. 确认 `qian/d3.v7.min.js` 文件是否存在
2. 确认文件大小是否为 273KB 左右
3. 尝试重新下载：
   ```bash
   cd "c:\Users\sanjin\Desktop\票务资金展示\qian"
   curl -o d3.v7.min.js https://d3js.org/d3.v7.min.js
   ```

### 问题 3：CDN 也加载失败
**现象**：网络断开时，图谱完全不显示

**解决方案**：
- 确保本地文件存在且完整
- 检查文件权限，确保 Web 服务器可以读取
- 清除浏览器缓存后重试

## 📝 使用说明

### 有网络连接时：
- 系统会自动优先加载本地 D3.js
- 如果本地文件损坏或缺失，自动切换到 CDN
- 无需任何手动操作

### 无网络连接时（离线环境）：
- 系统会加载本地 D3.js 文件
- 所有图谱功能正常使用
- 完全不需要网络

### 混合场景：
- 在公司有网时使用 CDN（可能更快）
- 在家或出差无网时使用本地文件
- 系统自动适配，无缝切换

## 🎯 验证清单

- [x] D3.js 本地文件已下载 (`qian/d3.v7.min.js`)
- [x] filter.html 已修改为支持本地 + CDN
- [x] detal.html 已修改为支持本地 + CDN
- [x] 测试页面已创建 (`test_d3.html`)
- [ ] 在有网络环境下测试通过
- [ ] 在无网络环境下测试通过
- [ ] 在所有主要浏览器（Chrome、Edge、Firefox）测试通过

## 💡 下一步建议

1. **立即测试**：
   ```
   http://localhost:8080/qian/test_d3.html
   ```

2. **断网测试**：
   - 关闭 WiFi/拔掉网线
   - 访问 filter.html 和 detal.html
   - 确认图谱功能正常

3. **生产环境部署**：
   - 将 `d3.v7.min.js` 一起打包部署
   - 确保所有用户都能离线使用

## 📞 需要帮助？

如果遇到问题，请提供：
1. 浏览器 Console 中的错误信息
2. 使用的访问方式（直接打开 or HTTP 服务器）
3. 网络状态（有线/无线/离线）
