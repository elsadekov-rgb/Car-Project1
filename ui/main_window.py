from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                             QTableView, QPushButton, QHBoxLayout, QMessageBox,
                             QHeaderView, QLabel, QComboBox, QLineEdit, QDialog, QFileDialog)
from PyQt6.QtCore import Qt, QAbstractTableModel
from database.models import Part, Brand, Model, PartCompatibility, get_session
from sqlalchemy.orm import joinedload
from ui.part_form import PartForm
import pandas as pd
from datetime import datetime


class PartsTableModel(QAbstractTableModel):
    def __init__(self, parts):
        super().__init__()
        self.parts = parts
        self.headers = ["ID", "артикул", "название", "производитель", "марка", "цена", "остаток"]

    def rowCount(self, parent=None):
        return len(self.parts)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            part = self.parts[index.row()]
            col = index.column()
            if col == 0: return str(part.id)
            if col == 1: return part.article
            if col == 2: return part.name
            if col == 3: return part.manufacturer or ""
            if col == 4:  # Марка
                brands = {comp.model.brand.name for comp in getattr(part, 'compatibilities', [])}
                return ", ".join(sorted(brands)) if brands else "—"
            if col == 5: return f"{part.price:.2f}" if part.price else "0.00"
            if col == 6: return str(part.stock_quantity)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("каталог запчастей автомобиля")
        self.resize(1450, 750)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.create_parts_tab()
        self.populate_test_data()

    def create_parts_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # филь 
        filter_layout = QHBoxLayout()
        self.brand_combo = QComboBox()
        self.brand_combo.setMinimumWidth(220)
        self.brand_combo.currentIndexChanged.connect(self.apply_filter)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("поиск по артикулу или названию")
        self.search_edit.textChanged.connect(self.apply_filter)

        filter_layout.addWidget(QLabel("марка авто:"))
        filter_layout.addWidget(self.brand_combo)
        filter_layout.addWidget(QLabel("поиск:"))
        filter_layout.addWidget(self.search_edit)
        layout.addLayout(filter_layout)

        # конпк
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+запчаст")
        edit_btn = QPushButton("редактировать")
        delete_btn = QPushButton("удалить")
        export_btn = QPushButton("экспорт в эксель")
        import_btn = QPushButton("импорт из эксель")      
        manage_btn = QPushButton("марки и модели")

        add_btn.clicked.connect(self.add_part)
        edit_btn.clicked.connect(self.edit_part)
        delete_btn.clicked.connect(self.delete_part)
        export_btn.clicked.connect(self.export_to_excel)
        import_btn.clicked.connect(self.import_from_excel)   
        manage_btn.clicked.connect(self.open_brand_model_form)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(manage_btn)
        layout.addLayout(btn_layout)

        # табл
        self.table_view = QTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.setAlternatingRowColors(True)
        layout.addWidget(self.table_view)

        self.load_brands()
        self.load_parts()
        self.tabs.addTab(tab, "каталог запчастей")

    def load_brands(self):
        db = get_session()
        try:
            brands = db.query(Brand).order_by(Brand.name).all()
            self.brand_combo.clear()
            self.brand_combo.addItem("Все марки", None)
            for brand in brands:
                self.brand_combo.addItem(brand.name, brand.id)
        finally:
            db.close()

    def apply_filter(self):
        brand_id = self.brand_combo.currentData()
        search_text = self.search_edit.text().strip()

        db = get_session()
        try:
            query = db.query(Part).options(
                joinedload(Part.compatibilities)
                .joinedload(PartCompatibility.model)
                .joinedload(Model.brand)
            )

            if brand_id is not None:
                query = query.join(PartCompatibility).join(Model).filter(Model.brand_id == brand_id)

            if search_text:
                query = query.filter(
                    (Part.article.ilike(f"%{search_text}%")) |
                    (Part.name.ilike(f"%{search_text}%"))
                )

            parts = query.distinct().all()
            self.model = PartsTableModel(parts)
            self.table_view.setModel(self.model)
        finally:
            db.close()

    def load_parts(self):
        self.apply_filter()

    def add_part(self):
        dialog = PartForm()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.brand_combo.setCurrentIndex(0)
            self.apply_filter()

    def edit_part(self):
        selection = self.table_view.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(self, "внимание", "выберите запчасть")
            return
        row = selection[0].row()
        part_id = self.model.parts[row].id

        db = get_session()
        try:
            part = db.query(Part).get(part_id)
            dialog = PartForm(part)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.apply_filter()
        finally:
            db.close()

    def delete_part(self):
        selection = self.table_view.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(self, "внимание", "выберите запчасть")
            return
        if QMessageBox.question(self, "подтверждение", "удалить эту запчасть?") != QMessageBox.StandardButton.Yes:
            return

        row = selection[0].row()
        part_id = self.model.parts[row].id

        db = get_session()
        try:
            part = db.query(Part).get(part_id)
            db.delete(part)
            db.commit()
            self.apply_filter()
        finally:
            db.close()

    def export_to_excel(self):
        try:
            db = get_session()
            parts = db.query(Part).options(
                joinedload(Part.compatibilities)
                .joinedload(PartCompatibility.model)
                .joinedload(Model.brand)
            ).all()

            data = [{
                "ID": p.id,
                "Артикул": p.article,
                "Название": p.name,
                "Производитель": p.manufacturer,
                "Марка": ", ".join(sorted({c.model.brand.name for c in getattr(p, 'compatibilities', [])})) or "—",
                "Цена": p.price,
                "Остаток": p.stock_quantity,
                "Описание": p.description
            } for p in parts]

            df = pd.DataFrame(data)
            filename = f"parts_catalog_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            df.to_excel(filename, index=False)
            QMessageBox.information(self, "успех", f"экспорт завершён\nФайл: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "ошибка", str(e))
        finally:
            if 'db' in locals():
                db.close()

    def import_from_excel(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "выберите файл Excel", "", "Excel Files (*.xlsx *.xls)"
        )
        if not file_name:
            return

        try:
            df = pd.read_excel(file_name)
            db = get_session()
            added = 0

            for _, row in df.iterrows():
                article = str(row.get('артикул', '')).strip()
                if not article:
                    continue

                if db.query(Part).filter_by(article=article).first():
                    continue  

                brand_name = str(row.get('марка', 'юез марки')).strip()
                brand = db.query(Brand).filter_by(name=brand_name).first()
                if not brand:
                    brand = Brand(name=brand_name)
                    db.add(brand)
                    db.commit()

                model = db.query(Model).filter_by(brand_id=brand.id).first()
                if not model:
                    model = Model(brand_id=brand.id, name=f"{brand_name} Model", year_from=2018, year_to=2025)
                    db.add(model)
                    db.commit()

                part = Part(
                    article=article,
                    name=str(row.get('название', '')),
                    manufacturer=str(row.get('производитель', '')),
                    price=float(row.get('цена', 0)),
                    stock_quantity=int(row.get('остаток', 0)),
                    description=str(row.get('описание', ''))
                )
                db.add(part)
                db.commit()

                comp = PartCompatibility(part_id=part.id, model_id=model.id)
                db.add(comp)
                db.commit()
                added += 1

            db.close()
            QMessageBox.information(self, "импорт", f"успешно добавлено {added} запчастей")
            self.apply_filter()

        except Exception as e:
            QMessageBox.critical(self, "ошибка импорта", f"{str(e)}")

    def populate_test_data(self):
        db = get_session()
        try:
            if db.query(Brand).count() > 0:
                return

           
            print("тест")
        finally:
            db.close()

    def open_brand_model_form(self):
        from ui.brand_model_form import BrandModelForm
        dialog = BrandModelForm(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_brands()