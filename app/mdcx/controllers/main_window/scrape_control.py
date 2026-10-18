"""刮削状态机的界面端口与控制器。

P5.2 引入端口本身，P5.3b 引入 `ScrapeController`：开始/停止按钮的状态判定与流转
（开始→停止→停止中→空闲）在控制器里，`self.Ui` 一律通过端口访问，不再被控制器
直接摸到。端口只负责「怎么画」，宿主 `MyMAinWindow` 是端口的实现方。

与 `02-目标架构.md` §4.8.2 的五方法设计相比，有两处按实测证据调整（见台账 D-09）：

1. **没有 `pushButton_stop_scrape` 控件**。开始与停止是同一对按钮
   （`pushButton_start_cap` / `pushButton_start_cap2`），停止态靠文本切换
   （`main_window.py` 里 `"■ 停止"`、`" ■ 停止中 "`），因此
   `set_start_button_text` 与 `set_stop_button_text` 合并为 `set_scrape_button_text`。
2. **`set_controls_enabled` 无法保序**。`reset_buttons_status` 里 `setEnabled`
   与 `emit` 是逐个控件交替的（`setEnabled` → `emit` → `setEnabled` → …），
   统一开关会把顺序打乱，所以改成逐控件的原子操作 `set_control`。

实现方是 `MyMAinWindow`（结构化实现，不继承本 Protocol）——这样不必给
2400 行的主窗口类增加一个基类，也不必为了"声明"而引入运行时依赖。
"""

from typing import Callable, Optional, Protocol

from mdcx.base.file import save_success_list
from mdcx.config.enums import Switch
from mdcx.config.manager import manager
from mdcx.core.scraper import cancel_scrape_async, get_remain_list, start_new_scrape
from mdcx.models.enums import FileMode
from mdcx.models.flags import Flags
from mdcx.signals import signal_qt
from mdcx.utils import executor


class ScrapeUiPort(Protocol):
    """控制器需要的界面能力。全部是"给定结果就画"，不含判断。"""

    def set_scrape_button_text(self, text: str) -> None:
        """设置开始/停止按钮的文本（两个页面上的同功能按钮一起改）。"""
        ...

    def set_control(
        self,
        name: str,
        *,
        enabled: Optional[bool] = None,
        visible: Optional[bool] = None,
        text: Optional[str] = None,
        emit: Optional[str] = None,
    ) -> None:
        """对单个控件执行指定动作，未指定的动作不做。

        参数顺序即执行顺序：`enabled` → `visible` → `text` → `emit`。
        必须逐控件调用、不能用批量接口——原实现里这两类动作是交替的。
        """
        ...

    def set_failed_list_text(self, text: str) -> None:
        """设置「一键重新刮削失败列表」按钮的文案。"""
        ...

    def apply_running_style(self) -> None:
        """切成"刮削中"样式（红色）。"""
        ...

    def apply_idle_style(self) -> None:
        """切成"空闲"样式（蓝色）。"""
        ...

    def get_scrape_button_text(self) -> str:
        """读开始/停止按钮当前的文本——按钮自己就是状态位。"""
        ...

    def ask_stop_confirm(self) -> bool:
        """弹「确定要停止刮削吗？」确认框；用户选「停止刮削」返回 True。"""
        ...

    def start_kill_threads_thread(self) -> None:
        """起一个后台线程去关线程池（本身立即返回，不等线程停）。"""
        ...


class ScrapeController:
    """开始/停止按钮的状态切换。判定与流转在这里，画界面全走端口。"""

    def __init__(self, ui: ScrapeUiPort):
        self._ui = ui

    def toggle_start_stop(self) -> None:
        if self._ui.get_scrape_button_text() == "开始":
            if not get_remain_list():
                start_new_scrape(FileMode.Default)
        elif self._ui.get_scrape_button_text() == "■ 停止":
            self.request_stop()

    def request_stop(self) -> None:
        if Switch.SHOW_DIALOG_STOP_SCRAPE in manager.config.switch_on:
            if not self._ui.ask_stop_confirm():
                return
        if self._ui.get_scrape_button_text() == "■ 停止":
            executor.run(save_success_list())
            Flags.rest_time_convert_ = Flags.rest_time_convert
            Flags.rest_time_convert = 0
            self._ui.set_scrape_button_text(" ■ 停止中 ")
            signal_qt.show_scrape_info("⛔️ 刮削停止中...")
            cancel_scrape_async()  # 只取消本次刮削的异步任务，不动封面加载等其他提交
            self._ui.start_kill_threads_thread()

    def enter_running_state(self) -> None:
        Flags.stop_other = True
        self._ui.set_scrape_button_text("■ 停止")
        self._ui.set_control("pushButton_select_media_folder", visible=False)
        self._ui.set_control("pushButton_start_single_file", enabled=False, text="正在刮削中...")
        self._ui.set_control("pushButton_add_sub_for_all_video", enabled=False, text="正在刮削中...")
        self._ui.set_control("pushButton_show_pic_actor", enabled=False, text="刮削中...")
        self._ui.set_control("pushButton_add_actor_info", enabled=False, text="正在刮削中...")
        self._ui.set_control("pushButton_add_actor_pic", enabled=False, text="正在刮削中...")
        self._ui.set_control("pushButton_add_actor_pic_kodi", enabled=False, text="正在刮削中...")
        self._ui.set_control("pushButton_del_actor_folder", enabled=False, text="正在刮削中...")
        # self.Ui.pushButton_check_and_clean_files.setEnabled(False)
        self._ui.set_control("pushButton_check_and_clean_files", text="正在刮削中...")
        self._ui.set_control("pushButton_move_mp4", enabled=False, text="正在刮削中...")
        self._ui.set_control("pushButton_find_missing_number", enabled=False, text="正在刮削中...")
        self._ui.apply_running_style()

    def enter_idle_state(self, reset_threads_list: Callable[[], None]) -> None:
        self._ui.set_control("pushButton_start_cap", enabled=True)
        self._ui.set_control("pushButton_start_cap2", enabled=True)
        self._ui.set_control("pushButton_start_cap", emit="开始")
        self._ui.set_control("pushButton_start_cap2", emit="开始")
        self._ui.set_control("pushButton_select_media_folder", visible=True)
        self._ui.set_control("pushButton_start_single_file", enabled=True)
        self._ui.set_control("pushButton_start_single_file", emit="刮削")
        self._ui.set_control("pushButton_add_sub_for_all_video", enabled=True)
        self._ui.set_control("pushButton_add_sub_for_all_video", emit="点击检查所有视频的字幕情况并为无字幕视频添加字幕")
        self._ui.set_control("pushButton_show_pic_actor", enabled=True)
        self._ui.set_control("pushButton_show_pic_actor", emit="查看")
        self._ui.set_control("pushButton_add_actor_info", enabled=True)
        self._ui.set_control("pushButton_add_actor_info", emit="开始补全")
        self._ui.set_control("pushButton_add_actor_pic", enabled=True)
        self._ui.set_control("pushButton_add_actor_pic", emit="开始补全")
        self._ui.set_control("pushButton_add_actor_pic_kodi", enabled=True)
        self._ui.set_control("pushButton_add_actor_pic_kodi", emit="开始补全")
        self._ui.set_control("pushButton_del_actor_folder", enabled=True)
        self._ui.set_control("pushButton_del_actor_folder", emit="清除所有.actors文件夹")
        self._ui.set_control("pushButton_check_and_clean_files", enabled=True)
        self._ui.set_control("pushButton_check_and_clean_files", emit="点击检查待刮削目录并清理文件")
        self._ui.set_control("pushButton_move_mp4", enabled=True)
        self._ui.set_control("pushButton_move_mp4", emit="开始移动")
        self._ui.set_control("pushButton_find_missing_number", enabled=True)
        self._ui.set_control("pushButton_find_missing_number", emit="检查缺失番号")
        self._ui.apply_idle_style()
        Flags.file_mode = FileMode.Default
        reset_threads_list()
        if len(Flags.failed_list):
            self._ui.set_failed_list_text(f"一键重新刮削当前 {len(Flags.failed_list)} 个失败文件")
        else:
            self._ui.set_failed_list_text("当有失败任务时，点击可以一键刮削当前失败列表")
