# CGT Intelligence

国内遗传病基因检测企业动态情报平台。静态 GitHub Pages 网页，公开 RSS 检索，GitHub Actions 北京时间每日 08:00 左右自动更新。

## 上线
1. 仓库 Settings → Pages → Source 选择 **GitHub Actions**。
2. Settings → Actions → General → Workflow permissions 选择 **Read and write permissions**（如组织策略允许）。
3. Actions → **Refresh intelligence and deploy Pages** → Run workflow。
4. 打开 https://hjx-zju.github.io/cgt-intelligence/

## 数据质量
采集的 Google News RSS 是**待核验线索**，不能等同官方公告。只有人工逐项检查并写入 data/verified.json 的记录才能标记为已核验（须有 reviewed_by、reviewed_at、official_source）。抓取故障单独标注，不应视作“无重要新增”。初始库为空，首次采集后可能出现待核验候选。

## 本地预览
在仓库目录运行 `python -m http.server 8000`，打开 http://localhost:8000 。

## 维护
- data/companies.json：添加企业
- data/verified.json：人工核验事件
- scripts/collect.py：每天公开 RSS 信息检索
- data/events.json：自动生成并积累事件候选

公开仓库中的全部 JSON 均对所有访问者可见，请勿写入个人信息、凭据或非公开信息。
