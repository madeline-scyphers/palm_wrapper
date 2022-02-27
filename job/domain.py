from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd
import numpy as np

from .utils import get_factors_rev


def calc_plot_size(domain_x, domain_y, plot_goal, house_goal):
    f1 = sorted(get_factors_rev(domain_x))
    f2 = sorted(get_factors_rev(domain_y))
    try:
        plot_x, plot_y = None, None
    except IndexError:
        return
    for x in f1:
        for y in f2:
            if x * y - house_goal >= 0 and plot_goal - x * y >= 0:
                if not plot_x and not plot_y:
                    plot_x, plot_y = x, y
                if ((plot_goal - x * y) < (plot_goal - plot_x * plot_y)):
                    plot_x, plot_y = x, y 
                elif (((plot_goal - x * y) == (plot_goal - plot_x * plot_y))
                      and ((x - y) < (plot_x - plot_y))):
                    plot_x, plot_y = x, y
    return plot_x, plot_y

def calc_plot_sizes(domain_x, domain_y, plot_footprint, house_footprint, plot_ratio, dx, dy, x_spread=(-10, 0), y_spread=(-5, 30)):
    goal = plot_footprint / (dx * dy)
    house_goal = house_footprint / (dx * dy)
    dom_x = range(domain_x + x_spread[0], domain_x + x_spread[1] + 1)
    dom_y = range(domain_y + y_spread[0], domain_y + y_spread[1] + 1)
    plots = []
    for d_x in dom_x:
        for d_y in dom_y:
            # print(d_y, d_y * 0.7)
            trimmed_d_y = int(d_y * plot_ratio)
            plot_x, plot_y = calc_plot_size(d_x, trimmed_d_y, goal, house_goal)
            if plot_x is not None and plot_y is not None:
                plots.append((plot_x, plot_y, d_x, d_y, trimmed_d_y))
    return plots

def get_best_plot_size(plots, plot_footprint, plot_ratio, dx, dy):
    goal = plot_footprint / (dx * dy)
    tmp = pd.DataFrame(plots, columns=["px", "py", "dx", "dy", "trimmed_dy"])
    tmp["plt_area"] = tmp["px"] * tmp["py"]
    tmp["goal_diff"] = goal - tmp.plt_area
    tmp["domain_y_diff"] = tmp.dy * plot_ratio - tmp.trimmed_dy
    tmp["trimmed_area"] = tmp["dx"] * tmp["trimmed_dy"]
    tmp["full_domain"] = tmp["dx"] * tmp["dy"]
    tmp["ratio_diff"] = abs((((tmp.trimmed_area + round(tmp.domain_y_diff * tmp.dx))) / tmp.full_domain - plot_ratio))
    # tmp["ratio_diff"] = abs(((tmp.trimmed_area) / tmp.full_domain - plot_ratio))
    tmp = tmp.sort_values(by=["goal_diff", "ratio_diff", "domain_y_diff", "trimmed_area"], ascending=[True, True, True, False])
    # tmp = tmp.sort_values(by=["goal_diff", "domain_y_diff", "trimmed_area"], ascending=[True, True, False])

    tplot_x, tplot_y, tdomain_x, tdomain_y, trimmed_y = tmp[["px", "py", "dx", "dy", "trimmed_dy"]].iloc[0]

    return tplot_x, tplot_y, tdomain_x, tdomain_y, trimmed_y


def calc_house_size(plot_x, plot_y, house_footprint, dx, dy):
    goal = house_footprint / (dx * dy)
    f1 = range(1, plot_x + 1)
    f2 = range(1, plot_y + 1)
    true_x, true_y = f1[0], f2[0]
    for x in f1:
        for y in f2:
            padded_x, padded_y = x - 0, y - 0
            nums = sorted([padded_x, padded_y])
            if nums[0] * 2 <  nums[1]:
                continue
            if (abs(goal - padded_x * padded_y)  < abs(goal - true_x * true_y)):
                true_x, true_y = padded_x, padded_y
            elif ((abs(goal - padded_x * padded_y)  == abs(goal - true_x * true_y)) 
                  and (abs(padded_x - padded_y) < abs(true_x - true_y))):
                true_x, true_y = padded_x, padded_y
    return true_x, true_y

class BaseDomainArea(ABC):
    subplot: Optional["BaseDomainArea"]
    x: int
    y: int
    z: Optional[int]
    matrix: np.ndarray

    def __str__(self) -> str:
        string = ""
        for row in self.matrix:
            string += f'{" ".join(str(int(pixel)) for pixel in row)}\n'
        return string

    @abstractmethod
    def get_matrix(self) -> np.ndarray:
        """Get the numpy matrix representation of the domain area"""

    def _validate_matrix_size(self, subplot):
        for value in ["x", "y"]:
            cell_val = getattr(self, value)
            subplot_val = getattr(subplot, value)
            if subplot_val and cell_val < subplot_val:
                raise ValueError(f"The {value} ({cell_val}) value of {self.__class__.__name__}"
                                 f" must be larger than the house ({subplot_val}) going on it!")
                
    def save_matrix(self, filename: str, matrix_name: str = None) -> None:
        matrix = self.matrix if matrix_name is None else getattr(self, matrix_name)
        np.savetxt(filename, matrix, delimiter=",")

class House(BaseDomainArea):
    def __init__(self, x: int, y: int, z: int) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.matrix = self.get_matrix()

    def get_matrix(self) -> np.ndarray:
        house = np.full((self.x, self.y), self.z)
        return house
        # house = np.full((self.y + 2 * self.y_padding, self.x + 2 * self.x_padding), self.z, dtype = int)
        # house[:,[*np.arange(self.x_padding).tolist(), *(-(np.arange(self.x_padding) + 1)).tolist()]] = 0
        # house[[*np.arange(self.y_padding).tolist(), *(-(np.arange(self.y_padding) + 1)).tolist()]] = 0
        # return house

class Road:
    pass

class Cell(BaseDomainArea):
    def __init__(self, subplot: House, x: int, y: int) -> None:
        self.subplot = subplot
        self.x = x
        self.y = y
        # self.tree_domain_fraction = tree_domain_fraction
        self._validate_matrix_size(subplot=self.subplot)
        self.matrix = self.get_matrix()
        # self.trees = self.get_trees()
        
        # if np.max(self.matrix + self.trees) > np.max(self.matrix):
            # raise TypeError("Invalid Configuration, Only valid configuration found when trees overlap with house matrix")

    def get_matrix(self) -> np.ndarray:
        left = (self.x - self.subplot.x) // 2
        top = (self.y - self.subplot.y) // 2
        plot =  np.zeros((self.x, self.y), dtype=int)
        plot[left:left + self.subplot.x, top:top + self.subplot.y] = self.subplot.matrix
        
        return plot
    
    def calc_perimeter(self, x: int, y: int):
        # offset = 4
        # inset_min, inset_max = x, self.matrix.shape[0] - x
        return 2 * x + 2 * y - 4

    # def get_trees(self):
    #     no_of_trees = self.matrix.size // self.tree_domain_fraction if self.tree_domain_fraction is not None else 0
    #     perimeter = self.calc_perimeter(self.x, self.y)

    #     trees_fence = self.set_fence(no_of_trees)
    #     return trees_fence

    # def set_fence(self, no_of_trees):
    #     a = np.zeros((self.y, self.x), dtype=int)
        
    #     for step in range(1, min(a.shape) // 2):
    #         a = self._set_fence(np.zeros((self.y, self.x), dtype=int), step)
    #         if a.sum() >= no_of_trees:
    #             break
    #     else:
    #         raise TypeError("Invalid number of trees")
        
    #     perimeter = a.sum()
        
    #     perim_locations = np.linspace(0, perimeter, num=no_of_trees, endpoint=False, dtype=int)
    #     perim_inds = np.where(a[a == 1])[0]
    #     a[a == 1] = np.where(np.isin(perim_inds, perim_locations), 1, 0)
    #     return a

    @staticmethod
    def _set_fence(a, step=0):
        a[((np.arange(0,step), np.arange(-step,0))),] = 1
        a[:,((np.arange(0,step), np.arange(-step,0)))] = 1
        return a

class Domain(BaseDomainArea):
    def __init__(self, subplot: Cell, tdomain_x, tdomain_y, full_x, full_y, trimmed_y, plot_ratio) -> None:
        self.subplot = subplot
        self.temp_x = tdomain_x
        self.temp_y = tdomain_y
        self.full_x = full_x
        self.full_y = full_y
        self.trimmed_y = trimmed_y
        self.plot_ratio = plot_ratio
        # self._validate_matrix_size(subplot=self.subplot)
        self.matrix, self.trees_matrix = self.get_matrix()
    
    def print_tree_matrix(self) -> str:
        string = ""
        for row in self.trees_matrix: 
            string += f'{" ".join(str(int(pixel)) for pixel in row)}\n'
        return string

    def get_matrix(self) -> np.ndarray:
        houses_row = np.tile(self.subplot.matrix, (self.temp_x // self.subplot.x, 1,))
        number_of_house_rows = self.trimmed_y // self.subplot.y
        number_of_full_tree_rows = int(self.temp_y * (1 - self.plot_ratio))
        mixed_row_ratio = self.temp_y * self.plot_ratio - self.trimmed_y
        
        tree_row = np.full((self.temp_x, 1), -1)
        mixed_row = np.array([-1 if i <= mixed_row_ratio * self.temp_x else 0 for i in range(1, self.temp_x + 1)]).reshape(self.temp_x, 1)
        
        rows = [[houses_row.copy()] for _ in range(number_of_house_rows)]
        trees = [tree_row.copy() for _ in range(number_of_full_tree_rows)]
        trees.insert(number_of_house_rows // 2, mixed_row)
        while trees:
            for row in rows:
                if not trees:
                    break
                row.append(trees.pop())

            
        domain_with_trees = np.concatenate([np.concatenate(row, axis=1) for row in rows], axis=1)
        
        dwtx = domain_with_trees.shape[0]
        dwty = domain_with_trees.shape[1]
        xs = int(np.floor((self.full_x - dwtx) / 2)), int(np.ceil((self.full_x - dwtx) / 2))
        full_domain = np.pad(domain_with_trees, (xs, (self.full_y - dwty, 0)))
        
        domain = np.where(full_domain != -1, full_domain, 0)
        trees = np.where(full_domain == -1, full_domain, 0)
        
        return domain.T, trees.T

    @classmethod
    def from_domain_config(cls, house, config):
        cell = Cell(house, tree_domain_fraction=config["trees"]["domain_fraction"], **config["plot_size"])
        x = config["domain"]["x"]
        y = config["domain"]["y"]
        return cls(subplot=cell, x=x, y=y)
    
    @classmethod
    def from_plot_size(cls, house, config, tplot_x, tplot_y, tdomain_x, tdomain_y, trimmed_y, plot_ratio):
        cell = Cell(house, x=tplot_x, y=tplot_y)
        # x = config["domain"]["x"]
        # y = config["domain"]["y"]
        return cls(cell, tdomain_x, tdomain_y, config["domain"]["x"], config["domain"]["y"], trimmed_y, plot_ratio)
    
def setup_domain(cfg):
    domain_x, domain_y = cfg["domain"]["x"], (round(cfg["domain"]["y"] * cfg["domain"]["urban_ratio"]))
    plot_footprint, plot_ratio, dx, dy = cfg["plot"]["plot_footprint"], cfg["plot"]["plot_ratio"], cfg["domain"]["dx"], cfg["domain"]["dy"]
    plots = calc_plot_sizes(domain_x, domain_y, plot_footprint, cfg["house"]["footprint"], plot_ratio, dx, dy,)
    tplot_x, tplot_y, tdomain_x, tdomain_y, trimmed_y = get_best_plot_size(plots, plot_footprint, plot_ratio, dx, dy)
    house_x, house_y = calc_house_size(tplot_x, tplot_y, cfg["house"]["footprint"], dx, dy)

    house = House(house_x, house_y, cfg["house"]["height"])

    return Domain.from_plot_size(house, cfg, tplot_x, tplot_y, tdomain_x, tdomain_y, trimmed_y, plot_ratio)
    # return Domain.from_domain_config(house, cfg)


if __name__ == "__main__":
    from .load_run_config import default_config
    config = default_config(
        # tree_domain_fraction=4,
    )
    domain = setup_domain(config)
    