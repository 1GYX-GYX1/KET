# 污染场地动态修复策略智能决策系统：公开演示版部署教程

## 这份包是做什么的
这不是论文真实模型的完整开源版，而是一个**公开演示版**。

它的作用是：
- 生成一个可以公开访问的平台链接
- 展示界面、输入项、动态监测、状态判定、建议结果和趋势图
- 不暴露真实训练数据、真实模型权重、私有知识先验和项目核心逻辑

这正好符合“可以公开演示，但不能泄露核心资产”的要求。

---

## 这个包里有什么

- `app_public_demo.py`：公开演示版主程序
- `requirements.txt`：部署依赖
- `.gitignore`：防止你误传敏感文件
- `README_公开演示版部署教程.md`：就是你现在看的说明

---

## 你不需要上传什么
下面这些东西**不要放进公开仓库**：

- `Dataset.csv`
- 任何训练数据表
- 任何真实案例原始数据
- `ket_rimtname_kah_prior_best_model.pth`
- `rimt_mapping.csv`
- 任何真实模型权重
- 任何真实知识先验矩阵
- 任何包含真实监测记录的 JSON 文件

---

## 最适合你的部署方式
建议你使用 **GitHub + Streamlit Community Cloud**。

优点：
- 不需要买服务器
- 不需要安装复杂环境
- 可以直接得到一个公网链接
- 操作几乎都可以在网页完成

---

## 第一步：注册 GitHub 账号
如果你还没有 GitHub 账号：
1. 打开 GitHub 官网
2. 注册账号
3. 登录

---

## 第二步：新建一个公开仓库
1. 登录 GitHub 后，点击右上角 `+`
2. 点击 `New repository`
3. Repository name 填：
   `contaminated-site-demo`
4. 选择 `Public`
5. 勾选 `Add a README file` 也可以，不勾也行
6. 点击 `Create repository`

---

## 第三步：上传这四个文件
进入你刚创建的仓库后：
1. 点击 `Add file`
2. 点击 `Upload files`
3. 把下面四个文件拖进去：
   - `app_public_demo.py`
   - `requirements.txt`
   - `.gitignore`
   - `README_公开演示版部署教程.md`
4. 页面下方 Commit message 可以写：
   `upload public demo version`
5. 点击 `Commit changes`

---

## 第四步：注册 Streamlit Community Cloud
1. 打开 Streamlit Community Cloud
2. 用 GitHub 账号登录
3. 首次登录时，授权它读取你的 GitHub 仓库

如果你后面想从**私有仓库**部署，需要额外授权私有仓库访问权限。

---

## 第五步：部署应用
1. 在 Streamlit Community Cloud 中点击 `Create app` 或 `Deploy an app`
2. 选择你刚刚创建的 GitHub 仓库：
   `contaminated-site-demo`
3. Branch 选 `main`
4. Main file path 填：
   `app_public_demo.py`
5. App URL 可以自己起一个简短名字，例如：
   `contaminated-site-demo-yanhao`
6. 点击 `Deploy`

等待几分钟后，系统会生成一个链接，例如：

`https://contaminated-site-demo-yanhao.streamlit.app`

这个就是你可以公开分享的平台演示链接。

---

## 第六步：如何更新平台
如果你之后想改页面内容：
1. 回到 GitHub 仓库
2. 点开 `app_public_demo.py`
3. 点击右上角铅笔图标编辑
4. 改完后点击 `Commit changes`
5. Streamlit 一般会自动重新部署
6. 刷新原来的链接即可看到新版本

---

## 第七步：论文里怎么写
你可以写成类似下面这种方式：

> A public demonstration interface of the platform is available online. Due to the confidentiality constraints of an ongoing project, the full training dataset, model weights, and core knowledge-enhanced assets are not publicly released.

这个表述比较稳妥。

---

## 如果你想进一步升级
后续你可以走两条路：

### 路线 A：继续保持公开演示版
优点：最安全，不泄露任何核心内容。

### 路线 B：公开界面 + 私有真实模型
做法：
- 公开仓库只保留前端页面
- 真实模型放在私有服务器
- 前端通过 API 调用私有模型

这样别人仍然只能看到平台和结果，看不到核心实现。

---

## 你后面如果想让我继续帮你做
你可以继续把下面任意一种内容发给我：

1. 你上传完 GitHub 后的截图，我一步一步带你点
2. 你希望我把这个演示版页面再改得更像你原始平台
3. 你想做“公开界面 + 私有真实模型”的下一版
4. 你想让我帮你写论文中的代码/数据可得性声明

