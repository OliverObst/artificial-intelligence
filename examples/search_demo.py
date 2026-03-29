from ai9414.search import SearchDemo

app = SearchDemo(node_count=16, seed=7)
app.load_example("default_sparse_graph")
app.show()
