from abc import ABC, abstractmethod
from typing import Any, Literal
import uuid

from pydantic import BaseModel, Field

from zhenxun.utils.pydantic_compat import model_dump

from .core.base import RenderableComponent


class EChartsTitle(BaseModel):
    text: str
    """图表主标题"""
    left: Literal["left", "center", "right"] = "center"
    """标题水平对齐方式"""


class EChartsAxis(BaseModel):
    type: Literal["category", "value", "time", "log"]
    """坐标轴类型"""
    data: list[Any] | None = None
    """类目数据"""
    show: bool = True
    """是否显示坐标轴"""


class EChartsSeries(BaseModel):
    type: str
    """系列类型 (e.g., 'bar', 'line', 'pie')"""
    data: list[Any]
    """系列数据"""
    name: str | None = None
    """系列名称，用于 tooltip 的显示"""
    label: dict[str, Any] | None = None
    """图形上的文本标签"""
    itemStyle: dict[str, Any] | None = None
    """图形样式"""
    barMaxWidth: int | None = None
    """柱条的最大宽度"""
    smooth: bool | None = None
    """是否平滑显示折线"""


class EChartsTooltip(BaseModel):
    trigger: Literal["item", "axis", "none"] = Field("item", description="触发类型")
    """触发类型"""


class EChartsGrid(BaseModel):
    left: str | None = None
    """grid 组件离容器左侧的距离"""
    right: str | None = None
    """grid 组件离容器右侧的距离"""
    top: str | None = None
    """grid 组件离容器上侧的距离"""
    bottom: str | None = None
    """grid 组件离容器下侧的距离"""
    containLabel: bool = True
    """grid 区域是否包含坐标轴的刻度标签"""


class BaseChartData(RenderableComponent, ABC):
    """所有图表数据模型的基类"""

    style_name: str | None = None
    """组件的样式名称"""
    chart_id: str = Field(
        default_factory=lambda: f"chart-{uuid.uuid4().hex}",
        description="图表的唯一ID，用于前端渲染",
    )
    """图表的唯一ID，用于前端渲染"""

    echarts_options: dict[str, Any] | None = None
    """原始ECharts选项，用于高级自定义"""

    @abstractmethod
    def build_option(self) -> dict[str, Any]:
        """将 Pydantic 模型序列化为 ECharts 的 option 字典。"""
        raise NotImplementedError

    def get_render_data(self) -> dict[str, Any]:
        """为图表组件定制渲染数据，动态构建最终的 option 对象。"""
        dumped_data = model_dump(self, exclude={"template_path"})
        if hasattr(self, "build_option"):
            dumped_data["option"] = self.build_option()
        return dumped_data

    def get_required_scripts(self) -> list[str]:
        """声明此组件需要 ECharts 库。"""
        return ["js/echarts.min.js"]


class EChartsData(BaseChartData):
    """统一的 ECharts 图表数据模型"""

    template_path: str = Field(..., exclude=True, description="图表组件的模板路径")
    """图表组件的模板路径"""
    title_model: EChartsTitle | None = Field(
        None, alias="title", description="标题组件"
    )
    """标题组件"""
    grid_model: EChartsGrid | None = Field(None, alias="grid", description="网格组件")
    """网格组件"""
    tooltip_model: EChartsTooltip | None = Field(
        None, alias="tooltip", description="提示框组件"
    )
    """提示框组件"""
    x_axis_model: EChartsAxis | None = Field(None, alias="xAxis", description="X轴配置")
    """X轴配置"""
    y_axis_model: EChartsAxis | None = Field(None, alias="yAxis", description="Y轴配置")
    """Y轴配置"""
    series_models: list[EChartsSeries] = Field(
        default_factory=list, alias="series", description="系列列表"
    )
    """系列列表"""
    legend_model: dict[str, Any] | None = Field(
        default_factory=dict, alias="legend", description="图例组件"
    )
    """图例组件"""
    raw_options: dict[str, Any] = Field(
        default_factory=dict, description="用于 set_option 的原始覆盖选项"
    )
    """用于 set_option 的原始覆盖选项"""

    background_image: str | None = Field(None, description="用于横向柱状图的背景图片")
    """用于横向柱状图的背景图片"""

    def build_option(self) -> dict[str, Any]:
        """将 Pydantic 模型序列化为 ECharts 的 option 字典。"""
        option: dict[str, Any] = {}
        key_map = {
            "title": "title_model",
            "grid": "grid_model",
            "tooltip": "tooltip_model",
            "xAxis": "x_axis_model",
            "yAxis": "y_axis_model",
            "series": "series_models",
            "legend": "legend_model",
        }
        for echarts_key, model_attr in key_map.items():
            model_instance = getattr(self, model_attr, None)
            if model_instance:
                if isinstance(model_instance, list):
                    option[echarts_key] = [
                        model_dump(m, exclude_none=True) for m in model_instance
                    ]
                elif isinstance(model_instance, BaseModel):
                    option[echarts_key] = model_dump(model_instance, exclude_none=True)
                else:
                    option[echarts_key] = model_instance
        option.update(self.raw_options)
        return option

    @property
    def title(self) -> str:
        """为模板提供一个简单的字符串标题，保持向后兼容性。"""
        return self.title_model.text if self.title_model else ""

    @property
    def template_name(self) -> str:
        return self.template_path
