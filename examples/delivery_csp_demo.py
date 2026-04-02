from ai9414.delivery_csp import DeliveryCSPDemo

app = DeliveryCSPDemo(example="weekday_schedule")
app.set_algorithm("backtracking_forward_checking")
app.show()
