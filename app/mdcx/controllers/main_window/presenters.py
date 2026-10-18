"""呈现层：把领域数据渲染到界面。

约定（见 02-目标架构.md §4.8.3）：presenter 只接受一个 ``ui_root``（``Ui_MDCx`` 实例），
通过属性名访问控件；除 ``QTreeWidgetItem``（构造树节点必须拿到类本身）外不 import PyQt5，
也不认识 ``MyMAinWindow``。
搬移规则：``MyMAinWindow`` 上保留同签名的转发方法，``Init_Singal`` 的 connect 目标名不变。

宿主状态不外泄的三种做法（P4 + P5.3a）：
- **迟到创建的对象当参数传**（``TreePresenter``）：``item_succ``/``item_fail`` 由 ``Init_Ui`` 在
  窗口构造之后创建，presenter 拿不到，宿主传进来。
- **回写宿主状态用 setter 回调**：``set_now_show_name``/``set_show_name``/``set_show_data``/
  ``set_file_main_open_path``/``set_img_path`` —— presenter 在原来那一行调用宿主赋值器，写回时机
  与搬移前逐字节一致（同一个 ``try`` 内、同一语句位置）。
- **宿主已有的输出信号由构造注入**（``MainInfoPresenter`` 的 ``set_pic_text``/``set_pic_pixmap``）：
  emit 打在同一个 ``SignalInstance`` 上，``init.py`` 里的 connect 关系不变。

P5.3a 搬入的 5 个方法之间会互相调用，因此调用方拿到的都是**宿主的同名转发方法**（作为参数传入），
presenter 之间不互相持引用。
"""

import os
import traceback

from PyQt5.QtWidgets import QTreeWidgetItem

from mdcx.config.enums import NfoInclude
from mdcx.config.manager import manager
from mdcx.core.nfo import write_nfo
from mdcx.image import get_pixmap
from mdcx.models.log_buffer import LogBuffer
from mdcx.models.types import CrawlersResult, FileInfo, OtherInfo
from mdcx.signals import signal_qt
from mdcx.utils import executor, get_current_time


class DetailPresenter:
    """详情区：海报/缩略图的缩放与贴图。"""

    def __init__(self, ui_root) -> None:
        self._ui = ui_root

    def set_pixmaps(self, poster_pix, thumb_pix) -> None:
        self._ui.label_poster.resize(poster_pix[3], poster_pix[4])
        self._ui.label_thumb.resize(thumb_pix[3], thumb_pix[4])

        if poster_pix[0]:
            self._ui.label_poster.setPixmap(poster_pix[1])
        else:
            self._ui.label_poster.setText(poster_pix[2])

        if thumb_pix[0]:
            self._ui.label_thumb.setPixmap(thumb_pix[1])
        else:
            self._ui.label_thumb.setText(thumb_pix[2])


class TipsPresenter:
    """提示区：主界面左下角的提示文本。"""

    def __init__(self, ui_root) -> None:
        self._ui = ui_root

    def show_tips(self, msg: str) -> None:
        self._ui.textBrowser_show_tips.setText(msg)
        self._ui.widget_show_tips.show()


class TreePresenter:
    """刮削结果树：把一条结果挂到成功/失败节点下。

    节点容器由宿主传入（它们由 ``Init_Ui`` 在窗口构造之后才创建，presenter 拿不到）。
    """

    def add_tree_child(self, result, filename, item_succ, item_fail) -> None:
        node = QTreeWidgetItem()
        node.setText(0, filename)
        if result == "succ":
            item_succ.addChild(node)
        else:
            item_fail.addChild(node)


class MainInfoPresenter:
    """主界面顶部信息区：番号/演员/标题等标签 + 封面缩略图。

    两个输出信号（``set_pic_text``/``set_pic_pixmap``）由宿主在构造时传入 —— 它们是
    ``MyMAinWindow`` 的类级 ``pyqtSignal``，连接关系属于宿主，presenter 只往上游发信号。
    """

    def __init__(self, ui_root, set_pic_text, set_pic_pixmap) -> None:
        self._ui = ui_root
        self.set_pic_text = set_pic_text
        self.set_pic_pixmap = set_pic_pixmap

    def set_main_info(
        self,
        show_data,
        set_show_data,
        set_show_name,
        set_file_main_open_path,
        set_img_path,
    ) -> None:
        if show_data is not None:
            set_show_data(show_data)
            file_info = show_data.file_info
            data = show_data.data
            other = show_data.other
            set_show_name(show_data.show_name)
        else:
            file_info = FileInfo.empty()
            data = CrawlersResult.empty()
            other = OtherInfo.empty()
            set_show_name(None)
        try:
            number = data.number
            self._ui.label_number.setToolTip(number)
            if len(number) > 11:
                number = number[:10] + "……"
            self._ui.label_number.setText(number)
            actor = str(data.actor)
            if data.all_actor and NfoInclude.ACTOR_ALL in manager.config.nfo_include_new:
                actor = str(data.all_actor)
            self._ui.label_actor.setToolTip(actor)
            if number and not actor:
                actor = manager.config.actor_no_name
            if len(actor) > 10:
                actor = actor[:9] + "……"
            self._ui.label_actor.setText(actor)
            set_file_main_open_path(file_info.file_path)  # 文件路径

            title = data.title.split("\n")[0].strip(" :")
            self._ui.label_title.setToolTip(title)
            if len(title) > 27:
                title = title[:25] + "……"
            self._ui.label_title.setText(title)
            outline = str(data.outline)
            self._ui.label_outline.setToolTip(outline)
            if len(outline) > 38:
                outline = outline[:36] + "……"
            self._ui.label_outline.setText(outline)
            tag = str(data.tag).strip(" [',']").replace("'", "")
            self._ui.label_tag.setToolTip(tag)
            if len(tag) > 76:
                tag = tag[:75] + "……"
            self._ui.label_tag.setText(tag)
            self._ui.label_release.setText(str(data.release))
            self._ui.label_release.setToolTip(str(data.release))
            if data.runtime:
                self._ui.label_runtime.setText(str(data.runtime) + " 分钟")
                self._ui.label_runtime.setToolTip(str(data.runtime) + " 分钟")
            else:
                self._ui.label_runtime.setText("")
            self._ui.label_director.setText(str(data.director))
            self._ui.label_director.setToolTip(str(data.director))
            series = str(data.series)
            self._ui.label_series.setToolTip(series)
            if len(series) > 32:
                series = series[:31] + "……"
            self._ui.label_series.setText(series)
            self._ui.label_studio.setText(data.studio)
            self._ui.label_studio.setToolTip(data.studio)
            self._ui.label_publish.setText(data.publisher)
            self._ui.label_publish.setToolTip(data.publisher)
            self._ui.label_poster.setToolTip("点击裁剪图片")
            self._ui.label_thumb.setToolTip("点击裁剪图片")
            # 生成img_path，用来裁剪使用
            img_path = other.fanart_path if other.fanart_path and other.fanart_path.is_file() else other.thumb_path
            set_img_path(img_path)
            if self._ui.checkBox_cover.isChecked():  # 主界面显示封面和缩略图
                poster_path = other.poster_path
                thumb_path = other.thumb_path
                fanart_path = other.fanart_path
                if not (thumb_path and thumb_path.is_file()) and fanart_path and fanart_path.is_file():
                    thumb_path = fanart_path
                poster_from = data.poster_from
                cover_from = data.thumb_from
                if poster_path and thumb_path:
                    executor.submit(self._set_pixmap(poster_path, thumb_path, poster_from, cover_from))
        except Exception:
            if not signal_qt.stop:
                signal_qt.show_traceback_log(traceback.format_exc())

    async def _set_pixmap(self, poster_path, thumb_path, poster_from="", cover_from=""):
        poster_pix = [False, "", "暂无封面图", 156, 220]
        thumb_pix = [False, "", "暂无缩略图", 328, 220]
        if os.path.exists(poster_path):
            poster_pix = await get_pixmap(poster_path, poster=True, pic_from=poster_from)
        if os.path.exists(thumb_path):
            thumb_pix = await get_pixmap(thumb_path, poster=False, pic_from=cover_from)

        # 原 label_poster_size 的那行注释已废弃（P5.3a 搬移时删除，见 HEAD main_window.py:894）
        poster_text = poster_pix[2] if poster_pix[2] != "暂无封面图" else ""
        thumb_text = thumb_pix[2] if thumb_pix[2] != "暂无缩略图" else ""
        self.set_pic_text.emit((poster_text + " " + thumb_text).strip())
        self.set_pic_pixmap.emit(poster_pix, thumb_pix)


class ScrapeListPresenter:
    """刮削结果列表：往结果树挂节点、点条目回填主界面。

    ``add_tree_child``/``set_main_info``/``show_nfo_info``/``set_show_name`` 都是宿主自己的
    转发方法或 setter，由调用点传入 —— 所以这里不需要认识 ``MyMAinWindow``。
    """

    def __init__(self, ui_root) -> None:
        self._ui = ui_root

    def show_list_name(
        self,
        status,
        show_data,
        real_number,
        add_tree_child,
        set_main_info,
        set_show_name,
        json_array,
    ) -> None:
        # 添加树状节点
        add_tree_child(status, show_data.show_name)

        if not show_data.data.title:
            show_data.data.title = LogBuffer.error().get()
            show_data.data.number = real_number
        set_show_name(show_data.show_name)
        set_main_info(show_data)
        json_array[show_data.show_name] = show_data

    def treeWidget_number_clicked(self, qmodeLindex, json_array, set_main_info, show_nfo_info) -> None:
        item = self._ui.treeWidget_number.currentItem()
        if item and item.text(0) != "成功" and item.text(0) != "失败":
            try:
                index_json = str(item.text(0))
                set_main_info(json_array[str(index_json)])
                if not self._ui.widget_nfo.isHidden():
                    show_nfo_info()
            except Exception:
                signal_qt.show_traceback_log(item.text(0) + ": No info!")


class NfoPresenter:
    """NFO 详情区：把一条 ``ShowData`` 渲染到 nfo 控件组，以及把编辑后的值写回 nfo 文件。"""

    def __init__(self, ui_root) -> None:
        self._ui = ui_root

    def show_nfo_info(self, show_name, json_array, set_now_show_name) -> None:
        try:
            if not show_name:
                return
            show_data = json_array[show_name]
            json_data = show_data.data
            file_info = show_data.file_info
            set_now_show_name(show_data.show_name)
            actor = json_data.actor
            if json_data.all_actor and NfoInclude.ACTOR_ALL in manager.config.nfo_include_new:
                actor = json_data.all_actor
            self._ui.label_nfo.setText(str(file_info.file_path))
            self._ui.lineEdit_nfo_number.setText(json_data.number)
            self._ui.lineEdit_nfo_actor.setText(actor)
            self._ui.lineEdit_nfo_year.setText(json_data.year)
            self._ui.lineEdit_nfo_title.setText(json_data.title)
            self._ui.lineEdit_nfo_originaltitle.setText(json_data.originaltitle)
            self._ui.textEdit_nfo_outline.setPlainText(json_data.outline)
            self._ui.textEdit_nfo_originalplot.setPlainText(json_data.originalplot)
            self._ui.textEdit_nfo_tag.setPlainText(json_data.tag)
            self._ui.lineEdit_nfo_release.setText(json_data.release)
            self._ui.lineEdit_nfo_runtime.setText(json_data.runtime)
            self._ui.lineEdit_nfo_score.setText(json_data.score)
            self._ui.lineEdit_nfo_wanted.setText(json_data.wanted)
            self._ui.lineEdit_nfo_director.setText(json_data.director)
            self._ui.lineEdit_nfo_series.setText(json_data.series)
            self._ui.lineEdit_nfo_studio.setText(json_data.studio)
            self._ui.lineEdit_nfo_publisher.setText(json_data.publisher)
            self._ui.lineEdit_nfo_poster.setText(json_data.poster)
            self._ui.lineEdit_nfo_cover.setText(json_data.thumb)
            self._ui.lineEdit_nfo_trailer.setText(json_data.trailer)
            all_items = [self._ui.comboBox_nfo.itemText(i) for i in range(self._ui.comboBox_nfo.count())]
            self._ui.comboBox_nfo.setCurrentIndex(all_items.index(json_data.country))
        except Exception:
            if not signal_qt.stop:
                signal_qt.show_traceback_log(traceback.format_exc())

    def save_nfo_info(self, now_show_name, json_array, set_main_info) -> None:
        try:
            if now_show_name is None:
                return
            show_data = json_array[now_show_name]
            json_data = show_data.data
            file_info = show_data.file_info
            nfo_path = file_info.file_path.with_suffix(".nfo")
            nfo_folder = nfo_path.parent
            json_data.number = self._ui.lineEdit_nfo_number.text()
            if NfoInclude.ACTOR_ALL in manager.config.nfo_include_new:
                json_data.all_actor = self._ui.lineEdit_nfo_actor.text()
            json_data.actor = self._ui.lineEdit_nfo_actor.text()
            json_data.year = self._ui.lineEdit_nfo_year.text()
            json_data.title = self._ui.lineEdit_nfo_title.text()
            json_data.originaltitle = self._ui.lineEdit_nfo_originaltitle.text()
            json_data.outline = self._ui.textEdit_nfo_outline.toPlainText()
            json_data.originalplot = self._ui.textEdit_nfo_originalplot.toPlainText()
            json_data.tag = self._ui.textEdit_nfo_tag.toPlainText()
            json_data.release = self._ui.lineEdit_nfo_release.text()
            json_data.runtime = self._ui.lineEdit_nfo_runtime.text()
            json_data.score = self._ui.lineEdit_nfo_score.text()
            json_data.wanted = self._ui.lineEdit_nfo_wanted.text()
            json_data.director = self._ui.lineEdit_nfo_director.text()
            json_data.series = self._ui.lineEdit_nfo_series.text()
            json_data.studio = self._ui.lineEdit_nfo_studio.text()
            json_data.publisher = self._ui.lineEdit_nfo_publisher.text()
            json_data.poster = self._ui.lineEdit_nfo_poster.text()
            json_data.thumb = self._ui.lineEdit_nfo_cover.text()
            json_data.trailer = self._ui.lineEdit_nfo_trailer.text()
            if executor.run(write_nfo(file_info, json_data, nfo_path, nfo_folder, update=True)):
                self._ui.label_save_tips.setText(f"已保存! {get_current_time()}")
                set_main_info(show_data)
            else:
                self._ui.label_save_tips.setText(f"保存失败! {get_current_time()}")
        except Exception:
            if not signal_qt.stop:
                signal_qt.show_traceback_log(traceback.format_exc())
