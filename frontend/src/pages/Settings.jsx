/**
 * Settings Page
 * User preferences and system configuration
 */
import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  User,
  Bell,
  Shield,
  Palette,
  Key,
  Globe,
  Moon,
  Sun,
  Copy,
  RefreshCw,
  Trash2,
  Plus,
  Loader2,
  Check,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const SAMPLE_API_KEYS = [
  { id: 'key-001', name: 'Production API Key', prefix: 'mtp_prod_', created: '2024-01-15', last_used: '2024-02-26', status: 'active' },
  { id: 'key-002', name: 'Development Key', prefix: 'mtp_dev_', created: '2024-02-01', last_used: '2024-02-25', status: 'active' },
  { id: 'key-003', name: 'Testing Key', prefix: 'mtp_test_', created: '2024-02-10', last_used: null, status: 'active' },
];

export default function Settings() {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [apiKeys, setApiKeys] = useState(SAMPLE_API_KEYS);
  const [newKeyDialogOpen, setNewKeyDialogOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    policyViolations: true,
    agentStatus: true,
    certExpiry: true,
    disputes: false,
  });

  const handleCreateKey = () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      const newKey = {
        id: `key-${Date.now()}`,
        name: newKeyName,
        prefix: 'mtp_new_',
        created: new Date().toISOString().split('T')[0],
        last_used: null,
        status: 'active',
      };
      setApiKeys(prev => [...prev, newKey]);
      setCreatedKey({
        ...newKey,
        fullKey: `mtp_new_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`,
      });
      setLoading(false);
    }, 1000);
  };

  const handleRevokeKey = (keyId) => {
    setApiKeys(prev => prev.filter(k => k.id !== keyId));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const saveSettings = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    }, 500);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400">Manage your account and preferences</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="bg-slate-800/50 border border-slate-700">
          <TabsTrigger value="profile" className="data-[state=active]:bg-blue-600">
            <User className="h-4 w-4 mr-2" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="notifications" className="data-[state=active]:bg-blue-600">
            <Bell className="h-4 w-4 mr-2" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="appearance" className="data-[state=active]:bg-blue-600">
            <Palette className="h-4 w-4 mr-2" />
            Appearance
          </TabsTrigger>
          <TabsTrigger value="api-keys" className="data-[state=active]:bg-blue-600">
            <Key className="h-4 w-4 mr-2" />
            API Keys
          </TabsTrigger>
          <TabsTrigger value="security" className="data-[state=active]:bg-blue-600">
            <Shield className="h-4 w-4 mr-2" />
            Security
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Profile Information</CardTitle>
              <CardDescription className="text-slate-400">Update your account details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-6">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-2xl font-bold">
                  {user?.name?.charAt(0) || 'U'}
                </div>
                <div>
                  <Button variant="outline" className="border-slate-700 text-slate-300">
                    Change Avatar
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-slate-200">Full Name</Label>
                  <Input
                    defaultValue={user?.name}
                    className="bg-slate-900/50 border-slate-700 text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-200">Email</Label>
                  <Input
                    defaultValue={user?.email}
                    disabled
                    className="bg-slate-900/50 border-slate-700 text-slate-400"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-200">Organization</Label>
                  <Input
                    defaultValue={user?.org}
                    disabled
                    className="bg-slate-900/50 border-slate-700 text-slate-400"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-200">Role</Label>
                  <Input
                    defaultValue={user?.role?.toUpperCase()}
                    disabled
                    className="bg-slate-900/50 border-slate-700 text-slate-400"
                  />
                </div>
              </div>

              <Button onClick={saveSettings} disabled={loading} className="bg-blue-600 hover:bg-blue-700">
                {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : saved ? <Check className="h-4 w-4 mr-2" /> : null}
                {saved ? 'Saved!' : 'Save Changes'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Notification Preferences</CardTitle>
              <CardDescription className="text-slate-400">Choose how you want to be notified</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium">Email Notifications</p>
                    <p className="text-sm text-slate-400">Receive notifications via email</p>
                  </div>
                  <Switch
                    checked={notifications.email}
                    onCheckedChange={(v) => setNotifications(prev => ({ ...prev, email: v }))}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium">Push Notifications</p>
                    <p className="text-sm text-slate-400">Browser push notifications</p>
                  </div>
                  <Switch
                    checked={notifications.push}
                    onCheckedChange={(v) => setNotifications(prev => ({ ...prev, push: v }))}
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-slate-700">
                <p className="text-white font-medium mb-4">Alert Types</p>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-300">Policy Violations</p>
                      <p className="text-sm text-slate-500">When an agent violates policies</p>
                    </div>
                    <Switch
                      checked={notifications.policyViolations}
                      onCheckedChange={(v) => setNotifications(prev => ({ ...prev, policyViolations: v }))}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-300">Agent Status Changes</p>
                      <p className="text-sm text-slate-500">Suspensions, activations, etc.</p>
                    </div>
                    <Switch
                      checked={notifications.agentStatus}
                      onCheckedChange={(v) => setNotifications(prev => ({ ...prev, agentStatus: v }))}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-300">Certification Expiry</p>
                      <p className="text-sm text-slate-500">30 days before expiration</p>
                    </div>
                    <Switch
                      checked={notifications.certExpiry}
                      onCheckedChange={(v) => setNotifications(prev => ({ ...prev, certExpiry: v }))}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-300">Dispute Updates</p>
                      <p className="text-sm text-slate-500">Status changes on disputes</p>
                    </div>
                    <Switch
                      checked={notifications.disputes}
                      onCheckedChange={(v) => setNotifications(prev => ({ ...prev, disputes: v }))}
                    />
                  </div>
                </div>
              </div>

              <Button onClick={saveSettings} disabled={loading} className="bg-blue-600 hover:bg-blue-700">
                {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : saved ? <Check className="h-4 w-4 mr-2" /> : null}
                {saved ? 'Saved!' : 'Save Preferences'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance Tab */}
        <TabsContent value="appearance">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Appearance</CardTitle>
              <CardDescription className="text-slate-400">Customize the dashboard appearance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">Theme</p>
                  <p className="text-sm text-slate-400">Choose between light and dark mode</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={toggleTheme}
                    className={theme === 'light' ? 'bg-blue-600 border-blue-600' : 'border-slate-700'}
                  >
                    <Sun className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={toggleTheme}
                    className={theme === 'dark' ? 'bg-blue-600 border-blue-600' : 'border-slate-700'}
                  >
                    <Moon className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                <div>
                  <p className="text-white font-medium">Language</p>
                  <p className="text-sm text-slate-400">Select your preferred language</p>
                </div>
                <Select defaultValue="en">
                  <SelectTrigger className="w-[180px] bg-slate-900/50 border-slate-700 text-white">
                    <Globe className="h-4 w-4 mr-2" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="af">Afrikaans</SelectItem>
                    <SelectItem value="zu">Zulu</SelectItem>
                    <SelectItem value="xh">Xhosa</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                <div>
                  <p className="text-white font-medium">Compact Mode</p>
                  <p className="text-sm text-slate-400">Reduce spacing for more content</p>
                </div>
                <Switch />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="api-keys">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-white">API Keys</CardTitle>
                <CardDescription className="text-slate-400">Manage your API keys for programmatic access</CardDescription>
              </div>
              <Button onClick={() => setNewKeyDialogOpen(true)} className="bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />
                Create Key
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {apiKeys.map((key) => (
                  <div key={key.id} className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-white font-medium">{key.name}</p>
                        <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/20">
                          {key.status}
                        </Badge>
                      </div>
                      <code className="text-sm text-slate-400 font-mono">{key.prefix}...****</code>
                      <p className="text-xs text-slate-500 mt-1">
                        Created {key.created} - Last used {key.last_used || 'Never'}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRevokeKey(key.id)}
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Security Settings</CardTitle>
              <CardDescription className="text-slate-400">Manage your account security</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium">Two-Factor Authentication</p>
                    <p className="text-sm text-slate-400">Add an extra layer of security</p>
                  </div>
                  <Button variant="outline" className="border-slate-700 text-slate-300">
                    Enable 2FA
                  </Button>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                  <div>
                    <p className="text-white font-medium">Change Password</p>
                    <p className="text-sm text-slate-400">Update your password</p>
                  </div>
                  <Button variant="outline" className="border-slate-700 text-slate-300">
                    Change
                  </Button>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                  <div>
                    <p className="text-white font-medium">Session Timeout</p>
                    <p className="text-sm text-slate-400">Auto-logout after inactivity</p>
                  </div>
                  <Select defaultValue="30">
                    <SelectTrigger className="w-[180px] bg-slate-900/50 border-slate-700 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      <SelectItem value="15">15 minutes</SelectItem>
                      <SelectItem value="30">30 minutes</SelectItem>
                      <SelectItem value="60">1 hour</SelectItem>
                      <SelectItem value="never">Never</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                  <div>
                    <p className="text-white font-medium">Active Sessions</p>
                    <p className="text-sm text-slate-400">Manage your active sessions</p>
                  </div>
                  <Button variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10">
                    Revoke All
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create API Key Dialog */}
      <Dialog open={newKeyDialogOpen} onOpenChange={(open) => {
        setNewKeyDialogOpen(open);
        if (!open) {
          setNewKeyName('');
          setCreatedKey(null);
        }
      }}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">
              {createdKey ? 'API Key Created' : 'Create New API Key'}
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              {createdKey
                ? 'Copy your API key now. You won\'t be able to see it again.'
                : 'Create a new API key for programmatic access.'}
            </DialogDescription>
          </DialogHeader>

          {createdKey ? (
            <div className="space-y-4">
              <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                <p className="text-sm text-green-400 mb-2">Your new API key:</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-white font-mono text-sm bg-slate-900 p-2 rounded">
                    {createdKey.fullKey}
                  </code>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => copyToClipboard(createdKey.fullKey)}
                    className="text-slate-400 hover:text-white"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <p className="text-sm text-yellow-400">
                Make sure to copy this key - you won't be able to see it again!
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label className="text-slate-200">Key Name</Label>
                <Input
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g., Production API Key"
                  className="bg-slate-900/50 border-slate-700 text-white"
                />
              </div>
            </div>
          )}

          <DialogFooter>
            {createdKey ? (
              <Button onClick={() => {
                setNewKeyDialogOpen(false);
                setCreatedKey(null);
                setNewKeyName('');
              }} className="bg-blue-600 hover:bg-blue-700">
                Done
              </Button>
            ) : (
              <>
                <Button
                  variant="outline"
                  onClick={() => setNewKeyDialogOpen(false)}
                  className="border-slate-700 text-slate-300"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateKey}
                  disabled={!newKeyName || loading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Create Key
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
