import os
import shutil
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QDoubleSpinBox, QSpinBox, QTextEdit, QPushButton,
                             QLabel, QFileDialog, QMessageBox, QHBoxLayout, QComboBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from database.models import Part, Brand, Model, PartCompatibility, get_session


class PartForm(QDialog):
    def __init__(self, part=None, parent=None):
        super().__init__(parent)
        self.part = part
        self.image_path = getattr(part, 'image_path', None)

        self.setWindowTitle("Добавить / Редактировать запчасть")
        self.resize(550, 680)
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.article_edit = QLineEdit(getattr(part, 'article', ''))
        self.name_edit = QLineEdit(getattr(part, 'name', ''))
        self.manufacturer_edit = QLineEdit(getattr(part, 'manufacturer', ''))
        self.price_edit = QDoubleSpinBox()
        self.price_edit.setMaximum(1000000)
        self.price_edit.setValue(getattr(part, 'price', 0))
        self.stock_edit = QSpinBox()
        self.stock_edit.setMaximum(10000)
        self.stock_edit.setValue(getattr(part, 'stock_quantity', 0))
        self.description_edit = QTextEdit(getattr(part, 'description', ''))

        self.brand_combo = QComboBox()
        self.load_brands()

        self.image_label = QLabel()
        self.image_label.setFixedSize(220, 220)
        self.image_label.setStyleSheet("border: 1px solid gray; background: #f0f0f0;")

        if self.image_path and os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path).scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label.setPixmap(pixmap)

        btn_load = QPushButton("Загрузить изображение")
        btn_load.clicked.connect(self.load_image)

        form.addRow("Артикул *:", self.article_edit)
        form.addRow("Название *:", self.name_edit)
        form.addRow("Производитель:", self.manufacturer_edit)
        form.addRow("Марка автомобиля:", self.brand_combo)
        form.addRow("Цена (руб):", self.price_edit)
        form.addRow("Остаток:", self.stock_edit)
        form.addRow("Описание:", self.description_edit)
        form.addRow("Изображение:", self.image_label)
        form.addRow("", btn_load)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        save_btn.clicked.connect(self.save_part)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def load_brands(self):
        db = get_session()
        try:
            brands = db.query(Brand).order_by(Brand.name).all()
            self.brand_combo.clear()
            self.brand_combo.addItem("— Выберите марку —", None)
            for b in brands:
                self.brand_combo.addItem(b.name, b.id)
        finally:
            db.close()

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "",
                                                    "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            os.makedirs("resources/images", exist_ok=True)
            dest = os.path.join("resources/images", os.path.basename(file_name))
            shutil.copy(file_name, dest)
            self.image_path = dest
            pixmap = QPixmap(dest).scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label.setPixmap(pixmap)

    def save_part(self):
        if not self.article_edit.text().strip() or not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Артикул и Название обязательны!")
            return

        brand_id = self.brand_combo.currentData()
        if not brand_id:
            QMessageBox.warning(self, "Ошибка", "Выберите марку автомобиля!")
            return

        db = get_session()
        try:
            if self.part:
                self.part.article = self.article_edit.text().strip()
                self.part.name = self.name_edit.text().strip()
                self.part.manufacturer = self.manufacturer_edit.text().strip()
                self.part.price = self.price_edit.value()
                self.part.stock_quantity = self.stock_edit.value()
                self.part.description = self.description_edit.toPlainText()
                if self.image_path:
                    self.part.image_path = self.image_path
            else:
                new_part = Part(
                    article=self.article_edit.text().strip(),
                    name=self.name_edit.text().strip(),
                    manufacturer=self.manufacturer_edit.text().strip(),
                    price=self.price_edit.value(),
                    stock_quantity=self.stock_edit.value(),
                    description=self.description_edit.toPlainText(),
                    image_path=self.image_path
                )
                db.add(new_part)
                db.commit()

               
                model = db.query(Model).filter_by(brand_id=brand_id).first()
                if not model:
                    model = Model(brand_id=brand_id, name=f"{self.brand_combo.currentText()} Model", 
                                 year_from=2018, year_to=2025)
                    db.add(model)
                    db.commit()

                comp = PartCompatibility(part_id=new_part.id, model_id=model.id)
                db.add(comp)

            db.commit()
            QMessageBox.information(self, "Успех", "Запчасть сохранена!")
            self.accept()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            db.close()