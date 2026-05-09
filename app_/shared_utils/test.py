
from __future__ import annotations

try:
	from .main import GRID_SIZE, Grid, GridCell, create_sample_grid, get_neighbors, manhattan
except ImportError:
	from main import GRID_SIZE, Grid, GridCell, create_sample_grid, get_neighbors, manhattan


def test_grid_shape() -> None:
	grid = create_sample_grid()
	assert len(grid.cells) == GRID_SIZE
	assert all(len(row) == GRID_SIZE for row in grid.cells)


def test_coordinate_alignment() -> None:
	grid = create_sample_grid()
	for row_index, row in enumerate(grid.cells):
		for col_index, cell in enumerate(row):
			assert (cell.row, cell.col) == (row_index, col_index)


def test_neighbors() -> None:
	grid = create_sample_grid()
	assert {(cell.row, cell.col) for cell in grid.get_neighbors(0, 0)} == {(1, 0), (0, 1)}
	assert {(cell.row, cell.col) for cell in grid.get_neighbors(5, 5)} == {(4, 5), (6, 5), (5, 4), (5, 6)}


def test_manhattan() -> None:
	assert manhattan((0, 0), (3, 4)) == 7
	assert manhattan((5, 5), (5, 5)) == 0


def test_sample_grid_fixture() -> None:
	grid = create_sample_grid()
	assert grid.get_cell(1, 3).is_hub is True
	assert grid.get_cell(2, 4).is_charging is True
	assert grid.get_cell(4, 0).is_medical_pickup is True
	assert grid.get_cell(3, 6).no_fly is True


def test_grid_validation() -> None:
	grid = create_sample_grid()
	assert isinstance(grid, Grid)
	assert isinstance(grid.get_cell(0, 0), GridCell)


def run_all_tests() -> None:
	test_grid_shape()
	test_coordinate_alignment()
	test_neighbors()
	test_manhattan()
	test_sample_grid_fixture()
	test_grid_validation()
	print("shared_utils tests passed")


if __name__ == "__main__":
	run_all_tests()