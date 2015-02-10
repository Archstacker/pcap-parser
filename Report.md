title: 网络数据包分析工具
speaker: ArchStacker
transition: kontext
files: /js/demo.js,/css/demo.css

[slide]
# 网络数据包分析工具

[slide]
## 需求分析
---
* 分析pcap数据包 {:&.moveIn}
* 大局观：站在流的角度
* 主要关注：HTTP数据包

[slide]
## 将数据包转成数据库文件
---
* TCP流重组 {:&.moveIn}
* HTTP协议解析

[slide]
## HTTP协议解析
---
* HTTP类型的分析 {:&.moveIn}
* HTTP header的解析
* gzip类型的解压
* 包含文件内容的类型的确定

[slide]
## 项目难点
---
* 不确定性 {:&.zoomIn}
    * 源和目的的不确定性 {:&.zoomIn}
    * 数据类型的不确定性(数据包类型、文件类型)
    * HTTP header个数的不确定性
* 表现方式
    * 应该做成什么样？ {:&.zoomIn}
    * 能做成什么样?
    * 如何在两者之间做出平衡？

[slide]
# 程序展示

[slide]
## 下步计划
---
* 全选、反选 {:&.fadeIn}
* 针对某一结果再此进行查询
* 数据内容导出
* 数据库合并
* 源按MAC统计
* 实时预览
* 分类统计
* 程序更加人性化（等待界面、未存提醒）
* 增加程序的准确性 

[slide]
## 高端功能
---
* 树状显示HTTP地址 {:&.fadeIn}
* cookie利用
* 访问重现
* 统计分析一类数据包进行处理
* HTTPS等加密访问的内容解析
