import os
import subprocess
import time
import glob
import ezdxf

class DxfDwgConverter:
    def __init__(self):
        pass

    # ODA 相关接口已禁用，不再使用

    def convert_dxf_to_dwg(self, input_files, output_dir, version="ACAD2018"):
        """Convert DXF files to DWG via AutoCAD COM."""
        return self.convert_with_autocad(input_files, output_dir, target_format="dwg")

    def convert_dwg_to_dxf(self, input_files, output_dir, version="ACAD2018"):
        """Convert DWG files to DXF via AutoCAD COM."""
        return self.convert_with_autocad(input_files, output_dir, target_format="dxf")
        
    def convert_dxf_version(self, input_files, output_dir, version="R2013"):
        """
        Convert DXF version using ezdxf (Native Python).
        Supported output versions: R12, R2000, R2004, R2007, R2010, R2013, R2018
        """
        success_count = 0
        errors = []
        
        # ezdxf version mapping
        ver_map = {
            "ACAD12": "R12",
            "ACAD2000": "R2000",
            "ACAD2004": "R2004",
            "ACAD2007": "R2007",
            "ACAD2010": "R2010",
            "ACAD2013": "R2013",
            "ACAD2018": "R2018"
        }
        
        dxf_version = ver_map.get(version, "R2013")
        
        for file_path in input_files:
            try:
                # Read
                try:
                    doc = ezdxf.readfile(file_path)
                except Exception as e:
                    errors.append(f"读取文件 {os.path.basename(file_path)} 失败: {e}")
                    continue
                
                # Save
                base_name = os.path.basename(file_path)
                output_file = os.path.join(output_dir, base_name)
                
                # Check if we need to rename to avoid overwrite if dir is same
                if os.path.abspath(output_dir) == os.path.abspath(os.path.dirname(file_path)):
                     name, ext = os.path.splitext(base_name)
                     output_file = os.path.join(output_dir, f"{name}_{dxf_version}{ext}")
                
                doc.saveas(output_file, encoding='utf-8', fmt='asc')
                success_count += 1
                
            except Exception as e:
                errors.append(f"转换 {os.path.basename(file_path)} 失败: {e}")
                
        if success_count > 0:
            return True, f"成功转换 {success_count} 个文件 (DXF版本更改)。"
        else:
            return False, f"转换失败: {'; '.join(errors)}"

    def convert_to_pdf(self, input_files, output_dir):
        """Convert DXF/DWG files to PDF via AutoCAD COM."""
        return self.convert_with_autocad(input_files, output_dir, target_format="pdf")

    def _clear_comtypes_cache(self):
        """Clear comtypes gen cache to fix import errors."""
        try:
            import comtypes
            gen_dir = comtypes.client._gen_dir
            if os.path.exists(gen_dir):
                import shutil
                shutil.rmtree(gen_dir)
                if not os.path.exists(gen_dir):
                    os.makedirs(gen_dir)
                # Re-initialize comtypes
                import importlib
                importlib.reload(comtypes)
                importlib.reload(comtypes.client)
                return True
        except Exception:
            return False
        return False

    def check_autocad_available(self, allow_create=False):
        """Check if AutoCAD is available via COM."""
        try:
            import comtypes.client
            # Try to connect to running instance
            comtypes.client.GetActiveObject("AutoCAD.Application")
            return True
        except ImportError:
            # Try clearing cache if import fails
            self._clear_comtypes_cache()
            try:
                import comtypes.client
                comtypes.client.GetActiveObject("AutoCAD.Application")
                return True
            except:
                return False
        except Exception:
            # Try clearing cache for other errors too (like module missing inside comtypes)
            if self._clear_comtypes_cache():
                try:
                    import comtypes.client
                    comtypes.client.GetActiveObject("AutoCAD.Application")
                    return True
                except:
                    pass
            
            if allow_create:
                try:
                    # Try to create new instance
                    import comtypes.client
                    comtypes.client.CreateObject("AutoCAD.Application")
                    return True
                except:
                    return False
            return False

    def convert_with_autocad(self, input_files, output_dir, target_format="dwg"):
        """
        Convert using AutoCAD COM automation.
        target_format: 'dwg' or 'dxf'
        """
        # Install COM IMessageFilter to gracefully handle "应用程序正在使用中" (RPC_E_CALL_REJECTED)
        # and auto-retry COM calls while AutoCAD is busy.
        def _register_message_filter():
            try:
                # Lazy imports to avoid hard dependency unless needed
                import comtypes
                from comtypes import COMMETHOD, GUID, IUnknown
                from ctypes import Structure, c_void_p, c_ushort, POINTER, byref, c_int, c_ulong, windll

                class INTERFACEINFO(Structure):
                    _fields_ = [
                        ("pUnk", c_void_p),
                        ("iid", GUID),
                        ("wMethod", c_ushort),
                    ]

                class IMessageFilter(IUnknown):
                    _iid_ = GUID("{00000016-0000-0000-C000-000000000046}")
                    _methods_ = [
                        COMMETHOD([], c_int, "HandleInComingCall",
                                  (["in"], c_ulong, "dwCallType"),
                                  (["in"], c_ulong, "htaskCaller"),
                                  (["in"], c_ulong, "dwTickCount"),
                                  (["in"], POINTER(INTERFACEINFO), "lpInterfaceInfo")),
                        COMMETHOD([], c_int, "RetryRejectedCall",
                                  (["in"], c_ulong, "htaskCallee"),
                                  (["in"], c_ulong, "dwTickCount"),
                                  (["in"], c_ulong, "dwRejectType")),
                        COMMETHOD([], c_int, "MessagePending",
                                  (["in"], c_ulong, "htaskCallee"),
                                  (["in"], c_ulong, "dwTickCount"),
                                  (["in"], c_ulong, "dwPendingType")),
                    ]

                # Constants from Win32
                SERVERCALL_ISHANDLED = 0
                SERVERCALL_REJECTED = 1
                SERVERCALL_RETRYLATER = 2

                PENDINGMSG_CANCELCALL = 0
                PENDINGMSG_WAITNOPROCESS = 1
                PENDINGMSG_WAITDEFPROCESS = 2

                class PythonMessageFilter(comtypes.COMObject):
                    _com_interfaces_ = [IMessageFilter]

                    def HandleInComingCall(self, dwCallType, htaskCaller, dwTickCount, lpInterfaceInfo):
                        return SERVERCALL_ISHANDLED

                    def RetryRejectedCall(self, htaskCallee, dwTickCount, dwRejectType):
                        if dwRejectType == SERVERCALL_RETRYLATER:
                            # Ask COM to retry after 150 ms
                            return 150
                        # Cancel for hard rejection
                        return -1

                    def MessagePending(self, htaskCallee, dwTickCount, dwPendingType):
                        # Let COM use default message loop handling
                        return PENDINGMSG_WAITDEFPROCESS

                new_filter = PythonMessageFilter()
                old_filter = POINTER(IMessageFilter)()
                windll.ole32.CoRegisterMessageFilter(new_filter._comobj, byref(old_filter))
                return (new_filter, old_filter)
            except Exception:
                return (None, None)

        def _unregister_message_filter(ctx):
            try:
                from ctypes import byref, windll, c_void_p
                if ctx and any(ctx):
                    windll.ole32.CoRegisterMessageFilter(c_void_p(0), byref(c_void_p()))
            except Exception:
                pass

        try:
            import comtypes.client
        except ImportError:
            self._clear_comtypes_cache()
            import comtypes.client
            
        try:
            # Register message filter to mitigate busy application errors
            _mf_ctx = _register_message_filter()

            try:
                acad = comtypes.client.GetActiveObject("AutoCAD.Application")
            except:
                try:
                    acad = comtypes.client.CreateObject("AutoCAD.Application")
                except Exception as e:
                    # Try clearing cache one last time
                    if self._clear_comtypes_cache():
                        try:
                            acad = comtypes.client.CreateObject("AutoCAD.Application")
                        except Exception as e2:
                            return False, f"无法启动 AutoCAD: {e2}"
                    else:
                        return False, f"无法启动 AutoCAD: {e}"
                
            # acad.Visible = True # Safer to make it visible
            acad.Visible = False # Run in background to avoid opening window
            
            doc = acad.Documents
            
            success_count = 0
            errors = []
            
            for file_path in input_files:
                try:
                    # Open file with retry for busy state
                    max_open_retries = 10
                    adoc = None
                    for i in range(max_open_retries):
                        try:
                            adoc = doc.Open(file_path)
                            break
                        except Exception as e_open:
                            msg = str(e_open)
                            # RPC_E_CALL_REJECTED (-2147417846): "应用程序正在使用中"
                            if "-2147417846" in msg or "正在使用中" in msg or "RPC_E_CALL_REJECTED" in msg:
                                time.sleep(0.2)
                                continue
                            raise

                    if adoc is None:
                        errors.append(f"文件 {os.path.basename(file_path)} 失败: 应用程序忙 (已重试{max_open_retries}次)")
                        continue
                    
                    try:
                        base_name = os.path.splitext(os.path.basename(file_path))[0]
                        output_file = os.path.join(output_dir, f"{base_name}.{target_format}")
                        
                        # SaveAs
                        # AcSaveAsType enum: 
                        # 60 = ac2013_dwg, 61 = ac2013_dxf
                        # 64 = ac2018_dwg, 65 = ac2018_dxf
                        
                        # Disable background plot to force synchronous operation
                        try:
                            # 0: Plotting in foreground
                            # 1: Silent background plotting
                            # 2: Background plotting
                            # 3: Silent + Background
                            adoc.SetVariable("BACKGROUNDPLOT", 0)
                        except Exception:
                            pass

                        if target_format.lower() == 'dwg':
                            save_type = 64 # 2018 DWG
                        elif target_format.lower() == 'dxf':
                            save_type = 65 # 2018 DXF
                        elif target_format.lower() == 'pdf':
                            # 对于 PDF，使用 Plot 接口而不是 SaveAs
                            # 使用重试机制来处理 Plot 操作
                            max_plot_retries = 10
                            plotted = False
                            saved = False # Initialize saved
                            
                            for p_i in range(max_plot_retries):
                                try:
                                    # 获取模型空间布局
                                    layout = adoc.ModelSpace.Layout
                                    
                                    # 配置打印设置
                                    layout.ConfigName = "DWG To PDF.pc3"
                                    layout.StandardScale = 0 
                                    layout.PlotType = 1
                                    layout.CenterPlot = True
                                    layout.PaperUnits = 1
                                    
                                    # 刷新打印设置
                                    layout.RefreshPlotDeviceInfo()
                                    
                                    # 执行打印
                                    adoc.Plot.PlotToFile(output_file)
                                    
                                    # 等待打印完成（简单的文件存在检查）
                                    # 由于 PlotToFile 是阻塞的（当前台打印时），理论上不需要太久的等待
                                    # 但为了保险，还是确认一下文件
                                    wait_start = time.time()
                                    while time.time() - wait_start < 30: # 最多等待30秒
                                        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                                            break
                                        time.sleep(0.5)
                                        
                                    plotted = True
                                    saved = True
                                    break
                                except Exception as e_plot:
                                    msg = str(e_plot)
                                    if "-2147417846" in msg or "正在使用中" in msg or "RPC_E_CALL_REJECTED" in msg:
                                        time.sleep(0.5) # 增加等待时间
                                        continue
                                    raise Exception(f"PDF 打印失败: {e_plot}")
                            
                            if not plotted:
                                raise Exception("PDF 打印操作超时或被拒绝")
                                
                        else:
                            raise ValueError(f"不支持的格式: {target_format}")
                            
                        if target_format.lower() != 'pdf':
                            # Save with retry for busy state
                            max_save_retries = 10
                            saved = False
                            for i in range(max_save_retries):
                                try:
                                    adoc.SaveAs(output_file, save_type)
                                    saved = True
                                    break
                                except Exception as e_save:
                                    msg = str(e_save)
                                    if "-2147417846" in msg or "正在使用中" in msg or "RPC_E_CALL_REJECTED" in msg:
                                        time.sleep(0.2)
                                        continue
                                    raise

                        if not saved:
                            errors.append(f"文件 {os.path.basename(file_path)} 失败: 保存阶段应用程序忙")
                            continue
                            
                    finally:
                        # Close with retry in finally block to ensure it always runs
                        if adoc:
                            for i in range(5):
                                try:
                                    adoc.Close(False)
                                    break
                                except Exception as e_close:
                                    msg = str(e_close)
                                    if "-2147417846" in msg or "正在使用中" in msg or "RPC_E_CALL_REJECTED" in msg:
                                        time.sleep(0.2)
                                        continue
                                    # If close still fails, attempt to detach and continue
                                    break
                    
                    success_count += 1
                except Exception as e:
                    errors.append(f"文件 {os.path.basename(file_path)} 失败: {e}")
                    
            if success_count > 0:
                _unregister_message_filter(_mf_ctx)
                return True, f"成功转换 {success_count} 个文件 (使用 AutoCAD)。"
            else:
                _unregister_message_filter(_mf_ctx)
                return False, f"转换失败: {'; '.join(errors)}"
                
        except Exception as e:
            try:
                _unregister_message_filter(_mf_ctx)
            except Exception:
                pass
            return False, f"AutoCAD 调用失败: {e}"

    def _run_oda_conversion(self, input_files, output_dir, output_format, version):
        """ODA 转换已禁用。"""
        return False, "已禁用 ODA File Converter。请使用 AutoCAD (COM) 执行 DWG/DXF 转换。"
