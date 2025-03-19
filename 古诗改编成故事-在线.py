import sys
import os
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel,
                             QTextEdit, QGridLayout, QWidget, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt
import random
import string
from datetime import datetime


class PoemStoryGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("古诗故事生成器")
        self.setGeometry(100, 100, 800, 600)

        # 创建中心部件和布局
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QGridLayout()
        widget.setLayout(layout)

        # 添加标题
        title_label = QLabel("根据古诗内容生成故事", self)
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label, 0, 0, 1, 2)

        # 输入框部分
        self._add_input_boxes(layout)

        # 生成按钮和保存按钮
        self.generate_btn = self._create_generate_button()
        self.save_btn = self._create_save_button()
        layout.addWidget(self.generate_btn, 4, 0, 1, 2, alignment=Qt.AlignCenter)
        layout.addWidget(self.save_btn, 5, 0, 1, 2, alignment=Qt.AlignCenter)

        # 输出结果框
        self._add_output_box(layout)

        # 版权信息
        self._add_copyright(layout)

    def _add_input_boxes(self, layout):
        # 古诗内容输入框
        poem_label = QLabel("请输入古诗内容：", self)
        self.poem_edit = QTextEdit()
        self.poem_edit.setPlaceholderText("例如：“床前明月光，疑是地上霜。”")
        self.poem_edit.setFixedHeight(100)
        layout.addWidget(poem_label, 1, 0)
        layout.addWidget(self.poem_edit, 1, 1)

        # 主要人物输入框
        characters_label = QLabel("故事主要人物及性格：", self)
        self.characters_edit = QTextEdit()
        self.characters_edit.setPlaceholderText("例如：“淘气的小孩儿”")
        self.characters_edit.setFixedHeight(100)
        layout.addWidget(characters_label, 2, 0)
        layout.addWidget(self.characters_edit, 2, 1)

        # 故事情节输入框
        plot_label = QLabel("主要故事情节：", self)
        self.plot_edit = QTextEdit()
        self.plot_edit.setPlaceholderText("简述故事的经过及结果，也可分条目详述。")
        self.plot_edit.setFixedHeight(100)
        layout.addWidget(plot_label, 3, 0)
        layout.addWidget(self.plot_edit, 3, 1)

    def _create_generate_button(self):
        generate_btn = QPushButton("生成故事", self)
        generate_btn.setToolTip("点击生成")
        generate_btn.clicked.connect(self.generateSTORY)
        return generate_btn

    def _create_save_button(self):
        save_btn = QPushButton("保存文本", self)
        save_btn.setToolTip("点击保存为 .txt 文件")
        save_btn.clicked.connect(self.saveGeneratedStory)
        return save_btn

    def _add_output_box(self, layout):
        # 输出结果框
        output_label = QLabel("生成的故事：", self)
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setMinimumHeight(500)
        layout.addWidget(output_label, 6, 0, Qt.AlignRight)
        layout.addWidget(self.output_edit, 6, 1, 3, 1)

    def _add_copyright(self, layout):
        # 在底部显示版权信息
        copyright_label = QLabel("@天津市南开区南开小学-7jul")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label, 9, 0, 1, 2)

    def generateSTORY(self):
        poem_content = self.poem_edit.toPlainText().strip()
        characters = self.characters_edit.toPlainText().strip()
        plot_description = self.plot_edit.toPlainText().strip()

        if not (poem_content and characters and plot_description):
            QMessageBox.warning(self, "输入错误", "请确保所有字段都已填写！")
            return

        # 构造提示
        prompt = f"""
        你是一个儿童文学作家，根据以下古诗内容、主要人物和故事情节，生成一个完整的故事：

        古诗内容：{poem_content}
        主要人物：{characters}
        故事情节：{plot_description}

        让故事基于这些元素展开，保持一致的风格，并且具有吸引力。
        """
        api_key = self._get_api_key()
        if not api_key:
            QMessageBox.warning(self, "API 密钥错误", "无法从 api.key 文件中读取 API 密钥！")
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "deepseek-reasoner",  # 或者尝试使用 "deepseek-reasoner"
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.8,
            "stream": False
        }

        try:
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                json=data,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                story = self._extract_story(result)
                if story:
                    # 隐去 <think> 中的文字内容
                    story = self._remove_think_content(story)
                    self.output_edit.setPlainText(story.strip())
                else:
                    QMessageBox.critical(self, "响应错误", "API 响应中没有找到故事内容！")
            else:
                QMessageBox.critical(self, "API 请求失败", f"状态码：{response.status_code}\n响应内容：{response.text}")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "网络错误", f"无法连接到 API：{e}")

    def _extract_story(self, response_json):
        """从 API 响应中提取生成的故事内容"""
        choices = response_json.get("choices", [])
        for choice in choices:
            message = choice.get("message", {})
            content = message.get("content", "")
            if content:
                return content.strip()
        return None

    def _remove_think_content(self, text):
        """从生成的故事中移除 <think></think> 中的内容"""
        start_tag = "<think>"
        end_tag = "</think>"
        start = text.find(start_tag)
        end = text.find(end_tag)
        if start != -1 and end != -1:
            cleaned_text = text[:start] + text[end + len(end_tag):]
            return cleaned_text
        return text

    def saveGeneratedStory(self):
        story_content = self.output_edit.toPlainText().strip()
        if not story_content:
            QMessageBox.warning(self, "保存警告", "没有内容可以保存，请先生成故事！")
            return

        # 生成文件名
        current_date = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        file_name = f"{current_date}_{random_str}.txt"

        # 保存内容到文件
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(story_content)
            QMessageBox.information(self, "保存成功", f"故事已保存至当前目录，文件名为：{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存过程中出错：{e}")

    def _get_api_key(self):
        """从 api.key 文件中读取 API 密钥"""
        api_key_file = "api.key"
        if not os.path.exists(api_key_file):
            return None

        try:
            with open(api_key_file, "r") as f:
                api_key = f.read().strip()
                return api_key
        except Exception as e:
            QMessageBox.critical(self, "API 密钥读取错误", f"读取 API 密钥时出错：{e}")
            return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = PoemStoryGenerator()
    main_window.show()
    sys.exit(app.exec())
