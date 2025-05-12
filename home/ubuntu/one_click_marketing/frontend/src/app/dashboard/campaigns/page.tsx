// frontend/src/app/dashboard/campaigns/page.tsx
"use client";

import { useState, useEffect, FormEvent, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { PlusCircle, Edit, Trash2, Eye, PlayCircle, CalendarIcon } from "lucide-react";
import { format, parseISO, isValid } from "date-fns";

interface Campaign {
  id: number;
  campaign_name: string;
  template_id: number;
  template_name?: string; // Optional, for display
  status: string;
  scheduled_at: string | null; // ISO string
  total_recipients: number;
  messages_sent_count: number;
  created_at: string; // ISO string
  updated_at: string; // ISO string
  audience_json?: string; // For edit form
  personalization_data_json?: string; // For edit form
}

interface MessageTemplate {
  id: number;
  template_name: string;
  status: string;
  // Add other relevant fields if needed for selection, e.g., category
}

const initialCampaignFormState = {
  id: 0,
  campaign_name: "",
  template_id: 0,
  audience_json: "[]", // Default to empty JSON array for phone numbers
  personalization_data_json: "{}", // Default to empty JSON object
  scheduled_at: null,
  status: "DRAFT", // Default status for new campaigns
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [messageTemplates, setMessageTemplates] = useState<MessageTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [currentCampaign, setCurrentCampaign] = useState<Campaign | null>(null);
  const [formData, setFormData] = useState<Omit<Campaign, "created_at" | "updated_at" | "messages_sent_count" | "template_name"> & { id?: number }>(initialCampaignFormState);
  const { toast } = useToast();

  const fetchCampaigns = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("authToken");
      if (!token) {
        toast({ title: "Authentication Error", variant: "destructive" });
        return;
      }
      const response = await fetch("/api/v1/campaigns", {
        headers: { "Authorization": `Bearer ${token}` },
      });
      if (response.ok) {
        const data: Campaign[] = await response.json();
        setCampaigns(data);
      } else {
        const errorData = await response.json();
        toast({ title: "Error fetching campaigns", description: errorData.message, variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "Network Error", variant: "destructive" });
    }
    setIsLoading(false);
  }, [toast]);

  const fetchTemplates = useCallback(async () => {
    // Fetch only approved templates for campaign creation
    try {
      const token = localStorage.getItem("authToken");
      if (!token) return;
      const response = await fetch("/api/v1/templates", {
        headers: { "Authorization": `Bearer ${token}` },
      });
      if (response.ok) {
        const data: MessageTemplate[] = await response.json();
        setMessageTemplates(data.filter(tpl => tpl.status === "APPROVED_BY_META"));
      } else {
        // Silently fail or show a non-blocking error for templates
        console.error("Failed to fetch message templates");
      }
    } catch (error) {
      console.error("Network error fetching templates", error);
    }
  }, []);

  useEffect(() => {
    fetchCampaigns();
    fetchTemplates();
  }, [fetchCampaigns, fetchTemplates]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };
  
  const handleDateTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    // Ensure value is either a valid ISO string or null
    setFormData(prev => ({ ...prev, [name]: value ? new Date(value).toISOString() : null }));
  };

  const handleFormSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    const token = localStorage.getItem("authToken");
    if (!token) {
      toast({ title: "Authentication Error", variant: "destructive" });
      setIsLoading(false);
      return;
    }

    if (!formData.template_id || formData.template_id === 0) {
        toast({ title: "Validation Error", description: "Please select a message template.", variant: "destructive" });
        setIsLoading(false);
        return;
    }

    try {
        JSON.parse(formData.audience_json || "[]");
        JSON.parse(formData.personalization_data_json || "{}");
    } catch (e) {
        toast({ title: "Invalid JSON", description: "Audience or Personalization Data is not valid JSON.", variant: "destructive" });
        setIsLoading(false);
        return;
    }

    const method = formData.id ? "PUT" : "POST";
    const url = formData.id ? `/api/v1/campaigns/${formData.id}` : "/api/v1/campaigns";
    
    const payload = {
        ...formData,
        template_id: Number(formData.template_id),
        scheduled_at: formData.scheduled_at ? formData.scheduled_at : null
    };

    try {
      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const responseData = await response.json();
      if (response.ok) {
        toast({ title: formData.id ? "Campaign Updated" : "Campaign Created", description: responseData.message });
        fetchCampaigns();
        setIsDialogOpen(false);
      } else {
        toast({ title: "Error", description: responseData.message || "An unknown error occurred.", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "Network Error", variant: "destructive" });
    }
    setIsLoading(false);
  };

  const handleEdit = (campaign: Campaign) => {
    setFormData({
      id: campaign.id,
      campaign_name: campaign.campaign_name,
      template_id: campaign.template_id,
      audience_json: campaign.audience_json || "[]",
      personalization_data_json: campaign.personalization_data_json || "{}",
      scheduled_at: campaign.scheduled_at ? new Date(campaign.scheduled_at).toISOString().substring(0, 16) : null, // Format for datetime-local
      status: campaign.status,
      total_recipients: campaign.total_recipients,
    });
    setIsDialogOpen(true);
  };
  
  const handleView = async (campaignId: number) => {
    setIsLoading(true);
    const token = localStorage.getItem("authToken");
    if (!token) { toast({ title: "Auth Error"}); setIsLoading(false); return; }
    try {
        const response = await fetch(`/api/v1/campaigns/${campaignId}`, { headers: { "Authorization": `Bearer ${token}`}});
        if (response.ok) {
            const data: Campaign = await response.json();
            setCurrentCampaign(data);
            setIsViewDialogOpen(true);
        } else {
            toast({ title: "Error fetching campaign details", variant: "destructive"});
        }
    } catch (e) {
        toast({ title: "Network error", variant: "destructive"});
    }
    setIsLoading(false);
  };

  const handleDelete = async (campaignId: number) => {
    if (!confirm("Are you sure you want to delete this campaign?")) return;
    setIsLoading(true);
    const token = localStorage.getItem("authToken");
    if (!token) { /* ... */ setIsLoading(false); return; }
    try {
      const response = await fetch(`/api/v1/campaigns/${campaignId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` },
      });
      const responseData = await response.json();
      if (response.ok) {
        toast({ title: "Campaign Deleted" });
        fetchCampaigns();
      } else {
        toast({ title: "Error Deleting Campaign", description: responseData.message, variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "Network Error", variant: "destructive" });
    }
    setIsLoading(false);
  };
  
  // Placeholder for a function to trigger campaign sending
  const handleSendCampaign = async (campaignId: number) => {
    toast({ title: "Send Action", description: `Triggering send for campaign ID ${campaignId} (not yet implemented).`});
    // This would typically call a backend endpoint like /api/v1/campaigns/${campaignId}/send
  };

  const openNewCampaignDialog = () => {
    setFormData(initialCampaignFormState);
    setIsDialogOpen(true);
  };

  return (
    <div className="container mx-auto p-4 md:p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Campaigns</h1>
        <Button onClick={openNewCampaignDialog}><PlusCircle className="mr-2 h-4 w-4" /> New Campaign</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your Campaigns</CardTitle>
          <CardDescription>Manage and launch your WhatsApp messaging campaigns.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading && campaigns.length === 0 ? (
            <p>Loading campaigns...</p>
          ) : campaigns.length === 0 ? (
            <p>No campaigns found. Click "New Campaign" to create one.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Template</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Scheduled At</TableHead>
                  <TableHead>Recipients</TableHead>
                  <TableHead>Sent</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {campaigns.map((camp) => (
                  <TableRow key={camp.id}>
                    <TableCell className="font-medium">{camp.campaign_name}</TableCell>
                    <TableCell>{camp.template_name || `ID: ${camp.template_id}`}</TableCell>
                    <TableCell>
                        <Badge variant={camp.status === "COMPLETED" ? "default" : camp.status === "SENDING" ? "outline" : "secondary"}
                               className={`${camp.status === "COMPLETED" ? "bg-green-500" : camp.status === "FAILED" ? "bg-red-500" : ""}`}
                        >
                            {camp.status.replace(/_/g, " ")}
                        </Badge>
                    </TableCell>
                    <TableCell>{camp.scheduled_at ? format(parseISO(camp.scheduled_at), "MMM d, yyyy HH:mm") : "-"}</TableCell>
                    <TableCell>{camp.total_recipients}</TableCell>
                    <TableCell>{camp.messages_sent_count}</TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button variant="outline" size="icon" onClick={() => handleView(camp.id)}><Eye className="h-4 w-4" /></Button>
                      {(camp.status === "DRAFT" || camp.status === "SCHEDULED") && 
                        <Button variant="outline" size="icon" onClick={() => handleEdit(camp)}><Edit className="h-4 w-4" /></Button>
                      }
                      {/* Add Send/Start button for DRAFT or PENDING_SEND campaigns */}
                      {(camp.status === "DRAFT" || camp.status === "PENDING_SEND" || camp.status === "SCHEDULED") && 
                        <Button variant="outline" size="icon" onClick={() => handleSendCampaign(camp.id)} title="Send/Start Campaign">
                            <PlayCircle className="h-4 w-4" />
                        </Button>
                      }
                      {(camp.status === "DRAFT" || camp.status === "SCHEDULED" || camp.status === "COMPLETED" || camp.status === "FAILED" || camp.status === "CANCELLED") &&
                        <Button variant="destructive" size="icon" onClick={() => handleDelete(camp.id)}><Trash2 className="h-4 w-4" /></Button>
                      }
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Campaign Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{formData.id ? "Edit" : "Create New"} Campaign</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleFormSubmit} className="space-y-4 py-4">
            <div>
              <Label htmlFor="campaign_name">Campaign Name</Label>
              <Input id="campaign_name" name="campaign_name" value={formData.campaign_name} onChange={handleInputChange} required />
            </div>
            <div>
              <Label htmlFor="template_id">Message Template (Approved by Meta)</Label>
              <Select name="template_id" value={String(formData.template_id)} onValueChange={(value) => handleSelectChange("template_id", Number(value))}>
                <SelectTrigger><SelectValue placeholder="Select an approved template" /></SelectTrigger>
                <SelectContent>
                  {messageTemplates.map(tpl => (
                    <SelectItem key={tpl.id} value={String(tpl.id)} disabled={tpl.status !== "APPROVED_BY_META"}>
                      {tpl.template_name} ({tpl.status.replace(/_/g, " ")})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="audience_json">Audience (JSON Array of Phone Numbers)</Label>
              <Textarea id="audience_json" name="audience_json" value={formData.audience_json} onChange={handleInputChange} rows={4} placeholder='[\"+15551230001\", \"+15551230002\"]' required />             <p className="text-xs text-gray-500 mt-1">Enter a list of phone numbers in international format.</p>
            </div>
            <div>
              <Label htmlFor="personalization_data_json">Personalization Data (JSON Object)</Label>
              <Textarea id="personalization_data_json" name="personalization_data_json" value={formData.personalization_data_json} onChange={handleInputChange} rows={6} placeholder='{
  "+15551230001": {"name": "Alice", "code": "1234"},
  "+15551230002": {"name": "Bob", "code": "5678"}
}' />
              <p className="text-xs text-gray-500 mt-1">Optional. Key is phone number, value is an object of variables for the template.</p>
            </div>
            <div>
              <Label htmlFor="scheduled_at">Schedule At (Optional)</Label>
              <Input id="scheduled_at" name="scheduled_at" type="datetime-local" value={formData.scheduled_at ? formData.scheduled_at.substring(0,16) : ""} onChange={handleDateTimeChange} />
              <p className="text-xs text-gray-500 mt-1">Leave blank to make campaign ready for manual sending, or set a future date/time.</p>
            </div>
            {(formData.id && formData.status) && (
                 <div>
                    <Label>Current Status</Label>
                    <Input value={formData.status.replace(/_/g, " ")} disabled />
                </div>
            )}
            <DialogFooter>
              <DialogClose asChild><Button type="button" variant="outline">Cancel</Button></DialogClose>
              <Button type="submit" disabled={isLoading}>{isLoading ? "Saving..." : (formData.id ? "Update Campaign" : "Create Campaign")}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Campaign Dialog */}
      {currentCampaign && (
        <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
            <DialogContent className="sm:max-w-lg">
                <DialogHeader>
                    <DialogTitle>View Campaign: {currentCampaign.campaign_name}</DialogTitle>
                    <DialogDescription>
                        Status: {currentCampaign.status} | Template: {currentCampaign.template_name || `ID ${currentCampaign.template_id}`}
                    </DialogDescription>
                </DialogHeader>
                <div className="py-4 space-y-3 text-sm">
                    <p><strong>Total Recipients:</strong> {currentCampaign.total_recipients}</p>
                    <p><strong>Messages Sent:</strong> {currentCampaign.messages_sent_count}</p>
                    {currentCampaign.scheduled_at && <p><strong>Scheduled At:</strong> {format(parseISO(currentCampaign.scheduled_at), "MMM d, yyyy HH:mm")}</p>}
                    <div>
                        <h4 className="font-semibold mt-2 mb-1">Audience:</h4>
                        <ScrollArea className="h-32 bg-gray-100 dark:bg-gray-800 p-2 rounded-md text-xs">
                            <pre>{currentCampaign.audience_json ? JSON.stringify(JSON.parse(currentCampaign.audience_json), null, 2) : "Not set"}</pre>
                        </ScrollArea>
                    </div>
                    <div>
                        <h4 className="font-semibold mt-2 mb-1">Personalization Data:</h4>
                        <ScrollArea className="h-32 bg-gray-100 dark:bg-gray-800 p-2 rounded-md text-xs">
                            <pre>{currentCampaign.personalization_data_json ? JSON.stringify(JSON.parse(currentCampaign.personalization_data_json), null, 2) : "Not set"}</pre>
                        </ScrollArea>
                    </div>
                    <p className="text-xs text-gray-500 mt-3">Created: {format(parseISO(currentCampaign.created_at), "MMM d, yyyy HH:mm")}</p>
                    <p className="text-xs text-gray-500">Last Updated: {format(parseISO(currentCampaign.updated_at), "MMM d, yyyy HH:mm")}</p>
                </div>
                <DialogFooter>
                    <DialogClose asChild><Button type="button" variant="outline">Close</Button></DialogClose>
                </DialogFooter>
            </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

