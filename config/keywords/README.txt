## 注意修改点

1. index

    1）id列 从 storage path 改成 document key

        在json array 的模式下， storage path 是相同的，所以索引只有一条记录。
        document key 是 storage path + record index，所以每条记录能区分开来。

    2） 删除document search key 列。

    3）配置每一列对应的属性， searchable， retrieval ，facet，filter 等。

    4） 配置senamic search的列

        默认是document search key，这个是产品的bug，目前在修复。

        增加page content 

        增加keyword 配置，把元数据作为 keyword 配置


**** 主要的问题：

    1. 没有vector 配置 （需要增加rag里面的skill）
    2. 没有title 列 （需要代码来处理）
    3. keyword 的打分函数的配置

