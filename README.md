# Waveform Review Kit｜通用波形人工筛选工具

[English documentation](README.en.md) · **简体中文**

> 本仓库已增加 [贡献指南](CONTRIBUTING.md)、[GitHub Actions 自动化测试](.github/workflows/tests.yml) 和 [合成演示界面截图脚本](tools/capture_demo.py)。截图由真实浏览器运行本地合成示例获取，**不是**真实地震观测数据，也不是 AI 生成的界面。



一个本地运行、数据与界面分离的波形浏览和人工复核项目。它保留了实际科研复核中最有用的流程：参考样本、待复核数据、多页波形、搜索与筛选、数字快捷键、备注、自动暂存，以及 CSV 导入导出。

界面只在本机浏览器中运行。默认监听 **127.0.0.1**，不会把波形或复核结果上传到互联网。

## 适用数据

当前版本面向“已经绘制成图片的波形数据”。支持 PNG、JPG、SVG、WebP 等浏览器可显示的图片。每条数据可以只有一张图，也可以包含多张台站分页图。

原始 SAC、miniSEED 或其他波形格式需要先按研究流程绘图，再交给本工具复核。这样不会把滤波、归一化、分量排列和拾取线画法强行固定在界面代码里。

## 30 秒运行演示

需要 Python 3.10 或更高版本，不需要安装第三方 Python 包。

Windows 可双击 **run_demo_windows.bat**，也可以运行：

~~~bash
python app.py --project examples/demo --open
~~~

macOS / Linux：

~~~bash
chmod +x run_demo_mac_linux.sh
./run_demo_mac_linux.sh
~~~

演示图全部由程序合成，不包含真实台站或地震数据。

## 用自己的数据建立项目

1. 复制 **examples/sample_input.csv**，每行填写一条待查看数据。
2. 将波形图片放在任意本地目录。
3. 运行构建工具：

~~~bash
python tools/build_project.py --csv /path/to/my_events.csv --assets-root /path/to --output /path/to/my_review_project --title "我的波形复核" --description "项目说明"
~~~

4. 启动复核网页：

~~~bash
python app.py --project /path/to/my_review_project --open
~~~

Windows 路径示例：

~~~powershell
python toolsuild_project.py --csv D:eviewevents.csv --assets-root D:eview --output D:eviewmy_project --title "我的波形复核"
python app.py --project D:eviewmy_project --open
~~~

构建工具会复制图片并生成 **project.json**。输入目录保持不变。若输出目录中已有清单或同名图片，程序默认停止；确认需要替换时再加 **--overwrite**。

## CSV 输入格式

必需列：

| 列名 | 含义 |
|---|---|
| id | 每条数据唯一编号 |
| image 或 images | 图片相对 --assets-root 的路径；多张图用竖线分隔 |

常用可选列：

| 列名 | 含义 |
|---|---|
| section | 数据分区；默认 review |
| title | 页面主标题；默认使用 id |
| subtitle | 简短说明 |
| tags | 多个标签用竖线分隔 |
| page_labels | 多张图片的页名，用竖线分隔 |
| meta_字段名 | 任意元数据，例如 meta_time、meta_magnitude |

默认把 known 和 candidate 分区设为只读参考区，其他分区可以人工判定。可用 **--reference-sections** 修改：

~~~bash
python tools/build_project.py ... --reference-sections reference,training
~~~

生成后可直接编辑 **project.json**，修改分区中文名、说明、判定类别和颜色。

## project.json 核心结构

~~~json
{
  "schema_version": 1,
  "project_id": "my-project",
  "title": "我的波形复核",
  "sections": [
    {"id": "review", "label": "待复核", "reviewable": true},
    {"id": "known", "label": "已知参考", "reviewable": false}
  ],
  "labels": [
    {"code": "confirmed", "name": "确认事件", "shortcut": "1", "color": "#248a3d"}
  ],
  "items": [
    {
      "id": "EVENT-001",
      "section": "review",
      "title": "EVENT-001",
      "subtitle": "候选事件说明",
      "tags": ["B级", "多页"],
      "metadata": {"时间": "2026-01-01 00:00:00", "台站数": 12},
      "pages": [
        {"image": "event001_page1.png", "label": "台站1–8"},
        {"image": "event001_page2.png", "label": "台站5–12"}
      ]
    }
  ]
}
~~~

图片路径相对于项目的 **assets/** 目录。

## 复核操作

- 左右方向键：上一条、下一条。
- 左右方括号：上一张、下一张波形页。
- 数字键：执行 project.json 中配置的判定。
- 数字 0：清除当前判定。
- 搜索：匹配编号、标题、说明、标签和元数据。
- 判定筛选：查看未复核、已复核或某一类结果。
- 标签筛选：只看某个质量级别或数据类别。
- 导出 CSV：输出全部可复核数据及当前判定。
- 导入复核结果：恢复本工具此前导出的 CSV。

数字快捷键在搜索框、下拉框和备注框中不会触发，避免输入备注时误判。

## 结果保存边界

判定与备注实时保存在当前浏览器的 localStorage 中，服务器只读。浏览器数据被清理、换浏览器或换电脑时，本地暂存不会自动迁移。因此应定期导出 CSV。导出的 CSV 可重新导入，也可以用 Excel、Python、R 或其他程序分析。

不同项目应使用不同的 project_id。同一项目若改变了数据含义，建议同时提高 schema_version，避免旧判定误套到新数据。

## 目录结构

~~~text
waveform-review-kit/
├─ app.py
├─ static/
│  ├─ index.html
│  ├─ app.js
│  └─ styles.css
├─ tools/
│  ├─ build_project.py
│  └─ generate_demo_assets.py
├─ examples/
│  ├─ demo/
│  │  ├─ project.json
│  │  └─ assets/
│  └─ sample_input.csv
├─ tests/
├─ run_demo_windows.bat
├─ run_demo_mac_linux.sh
└─ LICENSE
~~~

## 隐私与共享

发布代码时可以只分享程序和合成演示，不提交自己的 project.json、图片和导出结果。建议把真实数据项目放在本仓库目录之外，再通过 --project 指向它。

如果将监听地址改为 0.0.0.0，同一网络中的其他设备可能访问页面。多人同时复核时，每个浏览器仍各自保存判定，需要分别导出 CSV 后再合并。

## License

MIT

## GitHub 发布前保护

仓库默认忽略 projects、private_data、exports 目录，以及 SAC、miniSEED、PNG、JPG、TIFF、PDF、日志和复核结果 CSV。合成演示使用 SVG，因此仍会正常提交。真实数据请始终放在这些忽略目录或仓库之外；每次提交前运行 git status，确认待提交清单。
