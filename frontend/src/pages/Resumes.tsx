import { useState, useEffect } from 'react';
import { resumeAPI } from '../api';

export default function Resumes() {
  const [resumes, setResumes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [versionName, setVersionName] = useState('');

  useEffect(() => {
    loadResumes();
  }, []);

  const loadResumes = async () => {
    try {
      const res = await resumeAPI.list();
      setResumes(res.data || []);
    } catch (err) {
      console.error('Failed to load resumes', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('version_name', versionName || selectedFile.name);

    try {
      await resumeAPI.upload(formData);
      setSelectedFile(null);
      setVersionName('');
      await loadResumes();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this resume?')) return;
    try {
      await resumeAPI.delete(id);
      await loadResumes();
    } catch (err) {
      console.error('Delete failed', err);
    }
  };

  if (loading) return <div className="p-8 text-center">Loading...</div>;

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Resumes</h1>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="font-semibold mb-4">Upload Resume</h2>
        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
            />
            <p className="text-xs text-gray-500 mt-1">PDF or DOCX only</p>
          </div>
          <div>
            <input
              type="text"
              value={versionName}
              onChange={(e) => setVersionName(e.target.value)}
              placeholder="Version name (optional)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <button
            type="submit"
            disabled={!selectedFile || uploading}
            className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {uploading ? 'Uploading...' : 'Upload Resume'}
          </button>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow">
        <h2 className="font-semibold p-4 border-b">Your Resumes</h2>
        {resumes.length === 0 ? (
          <p className="p-4 text-gray-500">No resumes uploaded yet.</p>
        ) : (
          <ul className="divide-y">
            {resumes.map((resume) => (
              <li key={resume.id} className="p-4 flex justify-between items-center">
                <div>
                  <p className="font-medium">{resume.version_name || 'Untitled'}</p>
                  <p className="text-sm text-gray-500">
                    {resume.file_name} - Uploaded {new Date(resume.created_at).toLocaleDateString()}
                  </p>
                  {resume.is_primary && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Primary</span>
                  )}
                </div>
                <button
                  onClick={() => handleDelete(resume.id)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
