"""
Multi-Instance Manager View for BlueStacks Linux.
Enables creating, configuring, cloning, launching, and managing multiple Android instances.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog, QFormLayout,
                             QLineEdit, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal

from backend.instance_manager import instance_mgr, PRESETS
from backend.emulator_process import emulator
from config import config

class NewInstanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New BlueStacks Instance")
        self.resize(460, 320)
        vbox = QVBoxLayout(self)

        form = QFormLayout()

        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("e.g. bluestacks_instance_2")

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. BlueStacks Gaming 2")

        self.combo_preset = QComboBox()
        for k, v in PRESETS.items():
            self.combo_preset.addItem(v["name"], k)

        form.addRow("Instance ID:", self.input_id)
        form.addRow("Display Name:", self.input_name)
        form.addRow("Performance Preset:", self.combo_preset)

        vbox.addLayout(form)

        info = QLabel("💡 <b>Recommended:</b> Gaming Tablet (1600x900) provides 16:9 widescreen with Vulkan/virgl hardware acceleration.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #94A3B8; font-size: 11px;")
        vbox.addWidget(info)

        vbox.addStretch()

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_create = QPushButton("Create Instance")
        btn_create.setObjectName("PrimaryButton")
        btn_create.clicked.connect(self.accept)

        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_create)
        vbox.addLayout(btns)

    def get_data(self):
        aid = self.input_id.text().strip().replace(" ", "_").lower()
        dname = self.input_name.text().strip() or aid.replace("_", " ").title()
        preset_k = self.combo_preset.currentData()
        return aid, dname, preset_k

class InstanceView(QWidget):
    instance_started = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header controls
        top_bar = QHBoxLayout()
        title = QLabel("Android Instance Manager")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF;")

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh_instances)

        self.btn_new = QPushButton("➕ New Instance")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_new.clicked.connect(self.create_instance)

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_refresh)
        top_bar.addWidget(self.btn_new)
        layout.addLayout(top_bar)

        # Instances Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Instance Name", "Resolution", "RAM", "Cores", "Target", "Status", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.refresh_instances()

    def refresh_instances(self):
        instances = instance_mgr.list_instances()
        self.table.setRowCount(len(instances))

        for row, inst in enumerate(instances):
            # Name
            self.table.setItem(row, 0, QTableWidgetItem(f"{inst['display_name']} ({inst['id']})"))
            # Resolution
            self.table.setItem(row, 1, QTableWidgetItem(inst['resolution']))
            # RAM
            self.table.setItem(row, 2, QTableWidgetItem(f"{inst['ram_mb']} MB"))
            # Cores
            self.table.setItem(row, 3, QTableWidgetItem(f"{inst['cores']} vCPUs"))
            # Target
            self.table.setItem(row, 4, QTableWidgetItem(inst['target']))

            # Status pill
            status_item = QTableWidgetItem(inst['status'])
            if inst['status'] == "Running":
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 5, status_item)

            # Actions container
            action_widget = QWidget()
            act_layout = QHBoxLayout(action_widget)
            act_layout.setContentsMargins(4, 2, 4, 2)
            act_layout.setSpacing(6)

            if inst['status'] == "Running":
                btn_toggle = QPushButton("Stop")
                btn_toggle.setObjectName("DangerButton")
                btn_toggle.clicked.connect(lambda _, aid=inst['id']: self.stop_instance(aid))
            else:
                btn_toggle = QPushButton("Start")
                btn_toggle.setObjectName("PrimaryButton")
                btn_toggle.clicked.connect(lambda _, aid=inst['id']: self.start_instance(aid))

            btn_clone = QPushButton("📋")
            btn_clone.setToolTip("Clone Instance")
            btn_clone.setFixedWidth(32)
            btn_clone.clicked.connect(lambda _, aid=inst['id']: self.clone_instance(aid))

            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Delete Instance")
            btn_del.setFixedWidth(32)
            btn_del.setObjectName("DangerButton")
            btn_del.clicked.connect(lambda _, aid=inst['id']: self.delete_instance(aid))

            act_layout.addWidget(btn_toggle)
            act_layout.addWidget(btn_clone)
            act_layout.addWidget(btn_del)

            self.table.setCellWidget(row, 6, action_widget)

    def start_instance(self, avd_id: str):
        config.set("default_instance", avd_id)
        insts = instance_mgr.list_instances()
        target = [i for i in insts if i['id'] == avd_id]
        ram = target[0]['ram_mb'] if target else 3072
        cores = target[0]['cores'] if target else 4

        success = emulator.start(avd_id, gpu_mode=config.get("gpu_mode", "host"), ram_mb=ram, cores=cores)
        if success:
            self.instance_started.emit(avd_id)
            self.refresh_instances()
        else:
            QMessageBox.critical(self, "Error", f"Could not start instance: {avd_id}")

    def stop_instance(self, avd_id: str):
        emulator.stop(avd_id)
        self.refresh_instances()

    def clone_instance(self, src_id: str):
        new_id = f"{src_id}_clone"
        new_name = f"{src_id.replace('_', ' ').title()} Clone"
        if instance_mgr.clone_instance(src_id, new_id, new_name):
            QMessageBox.information(self, "Cloned", f"Instance cloned successfully as '{new_id}'!")
            self.refresh_instances()
        else:
            QMessageBox.critical(self, "Clone Failed", "Failed to clone instance.")

    def delete_instance(self, avd_id: str):
        if avd_id in instance_mgr.get_running_instances():
            QMessageBox.warning(self, "Running Instance", "Cannot delete a running instance. Stop it first.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to permanently delete '{avd_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            if instance_mgr.delete_instance(avd_id):
                self.refresh_instances()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete instance.")

    def create_instance(self):
        dlg = NewInstanceDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            aid, dname, preset = dlg.get_data()
            if not aid:
                QMessageBox.warning(self, "Invalid ID", "Please specify an Instance ID.")
                return
            if instance_mgr.create_instance(aid, dname, preset):
                QMessageBox.information(self, "Created", f"Instance '{dname}' created successfully!")
                self.refresh_instances()
            else:
                QMessageBox.critical(self, "Error", "Failed to create instance.")
