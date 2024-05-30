# 创建边DataFrame
edges = df.select(F.col("SENDER_WALLET").alias("src"), F.col("DESTINATION_TRANSACTION_HASH").alias("dst"), F.col("SOURCE_TIMESTAMP_UTC"))

# 创建节点DataFrame（即钱包）
nodes = df.select(F.col("SENDER_WALLET")).distinct().union(df.select(F.col("DESTINATION_TRANSACTION_HASH")).distinct())
nodes = nodes.withColumnRenamed("SENDER_WALLET", "id")

from graphframes import GraphFrame

# 创建图
g = GraphFrame(nodes, edges)

# 查找循环路径
cycles = g.find("(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)").filter("e1.SOURCE_TIMESTAMP_UTC < e2.SOURCE_TIMESTAMP_UTC AND e2.SOURCE_TIMESTAMP_UTC < e3.SOURCE_TIMESTAMP_UTC")

# 显示循环路径
cycles.show()