import { useState, useEffect } from 'react';
import { profileAPI } from '../api';

export default function Profile() {
  const [profile, setProfile] = useState({
    headline: '',
    target_roles: [] as string[],
    locations: [] as string[],
    seniority: '',
    remote_preference: '',
    sponsorship_needed: false,
  });
  const [rolesInput, setRolesInput] = useState('');
  const [locationsInput, setLocationsInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const res = await profileAPI.get();
      if (res.data) {
        setProfile({
          headline: res.data.headline || '',
          target_roles: res.data.target_roles || [],
          locations: res.data.locations || [],
          seniority: res.data.seniority || '',
          remote_preference: res.data.remote_preference || '',
          sponsorship_needed: res.data.sponsorship_needed || false,
        });
        setRolesInput((res.data.target_roles || []).join(', '));
        setLocationsInput((res.data.locations || []).join(', '));
      }
    } catch (err) {
      console.error('Failed to load profile', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    
    const profileData = {
      headline: profile.headline,
      target_roles: rolesInput.split(',').map(r => r.trim()).filter(Boolean),
      locations: locationsInput.split(',').map(l => l.trim()).filter(Boolean),
      seniority: profile.seniority,
      remote_preference: profile.remote_preference,
      sponsorship_needed: profile.sponsorship_needed,
    };
    
    try {
      await profileAPI.create(profileData);
      setMessage('Profile saved!');
    } catch (err: any) {
      if (err.response?.data?.detail?.includes('already exists')) {
        try {
          await profileAPI.patch(profileData);
          setMessage('Profile updated!');
        } catch {
          setMessage('Failed to update profile');
        }
      } else {
        setMessage('Failed to save profile');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 text-center">Loading...</div>;

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Profile</h1>
      
      {message && (
        <div className={`mb-4 p-3 rounded ${message.includes('saved') || message.includes('updated') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Professional Headline</label>
          <input
            type="text"
            value={profile.headline}
            onChange={(e) => setProfile({ ...profile, headline: e.target.value })}
            placeholder="e.g., Senior Software Engineer"
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Target Roles</label>
          <input
            type="text"
            value={rolesInput}
            onChange={(e) => setRolesInput(e.target.value)}
            placeholder="Software Engineer, Tech Lead (comma separated)"
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
          <p className="text-xs text-gray-500 mt-1">Separate multiple roles with commas</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Locations</label>
          <input
            type="text"
            value={locationsInput}
            onChange={(e) => setLocationsInput(e.target.value)}
            placeholder="Remote, San Francisco, New York (comma separated)"
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Seniority</label>
            <select
              value={profile.seniority}
              onChange={(e) => setProfile({ ...profile, seniority: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">Select...</option>
              <option value="entry">Entry</option>
              <option value="mid">Mid-level</option>
              <option value="senior">Senior</option>
              <option value="lead">Lead</option>
              <option value="principal">Principal</option>
              <option value="director">Director</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Remote Preference</label>
            <select
              value={profile.remote_preference}
              onChange={(e) => setProfile({ ...profile, remote_preference: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">No preference</option>
              <option value="remote">Remote only</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">On-site only</option>
            </select>
          </div>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="sponsorship"
            checked={profile.sponsorship_needed}
            onChange={(e) => setProfile({ ...profile, sponsorship_needed: e.target.checked })}
            className="mr-2"
          />
          <label htmlFor="sponsorship" className="text-sm text-gray-700">Visa sponsorship needed</label>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </form>
    </div>
  );
}
