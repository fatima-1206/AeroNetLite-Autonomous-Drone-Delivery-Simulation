# run the demo for showing the answer on what fleet selection we get on either genetic algo or brute force
# these can be selected
def run_demo(method: SelectionMethod | None = None) -> None:
	if method is not None:
		selected_method: SelectionMethod = method
	else:
		raw_method = sys.argv[1] if len(sys.argv) > 1 else "ga"
		if raw_method == "ga":
			selected_method = "ga"
		elif raw_method == "bf":
			selected_method = "bf"
		else:
			raise ValueError('method must be "ga" or "bf"')
	selection = select_fleet(random_seed=7, method=selected_method)
	print(f"Selected fleet using {selected_method}:", selection.to_dict())


if __name__ == "__main__":
	run_demo()
