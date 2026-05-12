from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QSpinBox, QPushButton, QMessageBox, QHBoxLayout,
                             QLabel, QComboBox)
from database.models import Brand, Model, get_session


class BrandModelForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚗 Добавить марку и модель")
        self.resize(520, 420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Мар
        self.brand_combo = QComboBox()
        self.load_brands()
        
        self.new_brand_edit = QLineEdit()
        self.new_brand_edit.setPlaceholderText("Введите новую марку (если нет в списке)")

        # Мод
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("Например: Camry, Corolla, 320i")

        self.year_from = QSpinBox()
        self.year_from.setRange(1950, 2030)
        self.year_from.setValue(2020)

        self.year_to = QSpinBox()
        self.year_to.setRange(1950, 2030)
        self.year_to.setValue(2025)

        form.addRow("Выбрать марку:", self.brand_combo)
        form.addRow("Или новая марка:", self.new_brand_edit)
        form.addRow("Название модели:", self.model_edit)
        form.addRow("Год с:", self.year_from)
        form.addRow("Год по:", self.year_to)

        layout.addLayout(form)

        # Кнопки
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        save_btn.clicked.connect(self.save_data)
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

    def save_data(self):
        db = get_session()
        try:
            # Опр марку
            if self.new_brand_edit.text().strip():
                brand_name = self.new_brand_edit.text().strip()
                brand = db.query(Brand).filter_by(name=brand_name).first()
                if not brand:
                    brand = Brand(name=brand_name)
                    db.add(brand)
                    db.commit()
            else:
                brand_id = self.brand_combo.currentData()
                if not brand_id:
                    QMessageBox.warning(self, "Ошибка", "Выберите или введите марку!")
                    return
                brand = db.query(Brand).get(brand_id)

            # моель
            model_name = self.model_edit.text().strip()
            if not model_name:
                QMessageBox.warning(self, "Ошибка", "Введите название модели!")
                return

            model = Model(
                brand_id=brand.id,
                name=model_name,
                year_from=self.year_from.value(),
                year_to=self.year_to.value()
            )
            db.add(model)
            db.commit()

            QMessageBox.information(self, "Успех", f"Модель «{model_name}» успешно добавлена!")
            self.accept()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            db.close()