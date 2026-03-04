import { useState, useRef, useEffect } from 'react';
import { 
  FileText, 
  File, 
  FileImage, 
  Download, 
  Trash2, 
  Search, 
  Upload, 
  X,
  FileSpreadsheet,
  Eye
} from 'lucide-react';
import { Document, User } from '../types';
import { documentService } from '../services/api';

interface ReferenceRoomProps {
  currentUser: User;
}

// Remove mock data
// const INITIAL_DOCUMENTS: Document[] = [...]

export default function ReferenceRoom({ currentUser }: ReferenceRoomProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState<Document | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Upload Form State
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadCategory, setUploadCategory] = useState('');
  const [uploadType, setUploadType] = useState<Document['type']>('pdf');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Load documents from API
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const data = await documentService.getAll();
        setDocuments(data);
      } catch (error) {
        console.error('Failed to fetch documents:', error);
      }
    };
    fetchDocuments();
  }, []);

  const CATEGORY_OPTIONS = [
    '电气资料',
    '机械资料',
    '规章制度',
    '财务报表',
    '会议纪要',
    '技术文档',
    '其他'
  ];

  const filteredDocs = documents.filter(doc => 
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (doc.category && doc.category.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleDelete = async (id: string) => {
    if (window.confirm('确定要删除这份资料吗？')) {
      try {
        await documentService.delete(id);
        setDocuments(prev => prev.filter(d => d.id !== id));
      } catch (error) {
        console.error('Failed to delete document:', error);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setUploadTitle(file.name);
      
      // Auto-detect type
      if (file.type.includes('pdf')) setUploadType('pdf');
      else if (file.type.includes('image')) setUploadType('image');
      else if (file.type.includes('sheet') || file.type.includes('excel')) setUploadType('xls');
      else if (file.type.includes('document') || file.type.includes('word')) setUploadType('doc');
      else if (file.type.includes('presentation') || file.type.includes('powerpoint')) setUploadType('ppt');
      else setUploadType('other');
    }
  };

  const handleUpload = async () => {
    if (!uploadTitle.trim()) return;
    
    let fileUrl = '#';
    let fileSize = '0 KB';

    if (selectedFile) {
      // Convert file to Base64 for persistence in json-server (db.json)
      // NOTE: This is suitable for small files in this demo environment.
      // Large files would bloat db.json significantly.
      try {
        const base64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.readAsDataURL(selectedFile);
          reader.onload = () => resolve(reader.result as string);
          reader.onerror = error => reject(error);
        });
        fileUrl = base64;
        fileSize = `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`;
      } catch (error) {
        console.error('Error converting file to base64:', error);
        return;
      }
    } else {
      // Fallback mock size for manual entry without file (if allowed, though we prefer file)
      fileSize = `${(Math.random() * 5 + 0.1).toFixed(1)} MB`;
    }

    const newDoc: Document = {
      id: Date.now().toString(),
      title: uploadTitle,
      type: uploadType,
      size: fileSize,
      uploadedBy: currentUser.name,
      uploadedAt: new Date().toISOString().slice(0, 10),
      url: fileUrl,
      category: uploadCategory || '未分类'
    };

    try {
      const createdDoc = await documentService.create(newDoc);
      setDocuments([createdDoc, ...documents]);
      setIsUploadOpen(false);
      setUploadTitle('');
      setUploadCategory('电气资料');
      setUploadType('pdf');
      setSelectedFile(null);
    } catch (error) {
      console.error('Failed to upload document:', error);
    }
  };

  const getIcon = (type: Document['type']) => {
    switch (type) {
      case 'pdf': return <FileText className="text-red-500" />;
      case 'xls': return <FileSpreadsheet className="text-green-500" />;
      case 'doc': return <FileText className="text-blue-500" />;
      case 'image': return <FileImage className="text-purple-500" />;
      default: return <File className="text-slate-500" />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 text-slate-800 relative">
      <header className="px-6 py-4 border-b border-slate-200 bg-white flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <span>首页</span>
          <span>/</span>
          <span className="text-slate-900 font-medium">资料室</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input 
              type="text" 
              placeholder="搜索资料..." 
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-9 pr-4 py-2 bg-slate-100 border-none rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
            />
          </div>
          <button 
            onClick={() => setIsUploadOpen(true)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Upload size={18} />
            <span className="text-sm font-medium">上传资料</span>
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        {filteredDocs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400">
            <File size={48} className="mb-4 opacity-20" />
            <p>暂无资料</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredDocs.map(doc => (
              <div key={doc.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-all group relative">
                <div className="flex items-start justify-between mb-3">
                  <div className="p-3 bg-slate-50 rounded-lg cursor-pointer" onClick={() => setPreviewDoc(doc)}>
                    {getIcon(doc.type)}
                  </div>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                    <button 
                      onClick={() => setPreviewDoc(doc)}
                      className="p-1.5 text-slate-400 hover:text-blue-500 hover:bg-blue-50 rounded"
                      title="预览"
                    >
                      <Eye size={16} />
                    </button>
                    {(currentUser.role === '管理员' || doc.uploadedBy === currentUser.name) && (
                      <button 
                        onClick={() => handleDelete(doc.id)}
                        className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded"
                        title="删除"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </div>
                
                <h3 
                  className="font-medium text-slate-800 mb-1 line-clamp-2 min-h-[44px] cursor-pointer hover:text-blue-600" 
                  title={doc.title}
                  onClick={() => setPreviewDoc(doc)}
                >
                  {doc.title}
                </h3>
                
                <div className="flex items-center gap-2 mb-3">
                  <span className="px-2 py-0.5 bg-slate-100 text-slate-500 text-xs rounded-full">
                    {doc.category || '未分类'}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400 pt-3 border-t border-slate-50">
                  <div className="flex flex-col gap-0.5">
                    <span>{doc.uploadedBy}</span>
                    <span>{doc.uploadedAt}</span>
                  </div>
                  <span>{doc.size}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {isUploadOpen && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md rounded-xl shadow-2xl p-6 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-slate-800">上传资料</h3>
              <button 
                onClick={() => setIsUploadOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">资料标题</label>
                <input 
                  type="text" 
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="请输入资料标题"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">资料类型</label>
                <select 
                  value={uploadType}
                  onChange={(e) => setUploadType(e.target.value as Document['type'])}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="pdf">PDF 文档</option>
                  <option value="doc">Word 文档</option>
                  <option value="xls">Excel 表格</option>
                  <option value="ppt">PPT 演示文稿</option>
                  <option value="image">图片</option>
                  <option value="other">其他</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">分类</label>
                <select 
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="" disabled>请选择分类</option>
                  {CATEGORY_OPTIONS.map(opt => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
              </div>

              <div 
                className="p-4 border-2 border-dashed border-slate-200 rounded-lg bg-slate-50 text-center text-slate-400 text-sm hover:border-blue-400 transition-colors cursor-pointer relative"
                onClick={() => fileInputRef.current?.click()}
              >
                <input 
                  type="file" 
                  className="hidden" 
                  ref={fileInputRef}
                  onChange={handleFileChange}
                />
                <Upload className="mx-auto mb-2 opacity-50" size={24} />
                <p>{selectedFile ? selectedFile.name : '点击选择文件或拖拽文件到此处'}</p>
                {selectedFile && <p className="text-xs mt-1 text-blue-500 font-medium">已选择文件</p>}
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button 
                  onClick={() => setIsUploadOpen(false)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  取消
                </button>
                <button 
                  onClick={handleUpload}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
                >
                  确认上传
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Preview Modal */}
      {previewDoc && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm p-4">
          <div className="bg-white w-full max-w-4xl h-[85vh] rounded-xl shadow-2xl flex flex-col animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-slate-100 rounded">
                  {getIcon(previewDoc.type)}
                </div>
                <h3 className="font-bold text-slate-800 line-clamp-1 max-w-md" title={previewDoc.title}>
                  {previewDoc.title}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <a 
                  href={previewDoc.url} 
                  download={previewDoc.title}
                  className="p-2 text-slate-500 hover:text-blue-600 hover:bg-slate-100 rounded-lg flex items-center gap-1 text-sm"
                >
                  <Download size={18} />
                  下载
                </a>
                <button 
                  onClick={() => setPreviewDoc(null)}
                  className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            
            <div className="flex-1 bg-slate-100 overflow-hidden flex items-center justify-center relative p-4">
              {previewDoc.type === 'image' ? (
                <img 
                  src={previewDoc.url} 
                  alt={previewDoc.title} 
                  className="max-w-full max-h-full object-contain shadow-lg rounded"
                />
              ) : previewDoc.type === 'pdf' ? (
                <iframe 
                  src={previewDoc.url} 
                  className="w-full h-full rounded shadow-sm bg-white"
                  title={previewDoc.title}
                />
              ) : (
                <div className="text-center text-slate-500">
                  <File size={64} className="mx-auto mb-4 opacity-20" />
                  <p className="text-lg font-medium mb-2">该文件类型不支持在线预览</p>
                  <p className="text-sm">请点击右上角下载按钮查看文件内容</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}