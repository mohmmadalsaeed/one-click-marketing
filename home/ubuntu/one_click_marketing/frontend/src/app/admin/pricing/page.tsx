// frontend/src/app/admin/pricing/page.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"; // For selecting clients

interface ClientPricingInfo {
  pricing_id?: number;
  client_id: number;
  username: string;
  email: string;
  price_per_message: string;
  currency: string;
  notes?: string;
  updated_at?: string;
}

interface UserClient {
    id: number;
    username: string;
    email: string;
}

export default function AdminPricingPage() {
  const [clientPricingList, setClientPricingList] = useState<ClientPricingInfo[]>([]);
  const [allClients, setAllClients] = useState<UserClient[]>([]); // For dropdown
  const [selectedClientId, setSelectedClientId] = useState<string>("");
  const [price, setPrice] = useState<string>("0.0100");
  const [currency, setCurrency] = useState<string>("USD");
  const [notes, setNotes] = useState<string>("");
  const [editingPricing, setEditingPricing] = useState<ClientPricingInfo | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const fetchAllClients = useCallback(async () => {
    const token = localStorage.getItem("authToken");
    if (!token) { /* ... */ return; }
    try {
        // Assuming an admin endpoint to list all client users
        const response = await fetch("/api/v1/admin/users?role=client", { 
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (response.ok) {
            const data = await response.json();
            setAllClients(data.users || []); 
        } else {
            toast({ title: "Error fetching client list", variant: "destructive" });
        }
    } catch (error) {
        toast({ title: "Network Error (Fetching Clients)", variant: "destructive" });
    }
  }, [toast]);

  const fetchClientPricingList = useCallback(async () => {
    setIsLoading(true);
    const token = localStorage.getItem("authToken");
    if (!token) { /* ... */ setIsLoading(false); return; }
    try {
      const response = await fetch("/api/v1/admin/pricing/clients", {
        headers: { "Authorization": `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setClientPricingList(data);
      } else {
        toast({ title: "Error fetching client pricing list", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "Network Error (Pricing List)", variant: "destructive" });
    }
    setIsLoading(false);
  }, [toast]);

  useEffect(() => {
    fetchAllClients();
    fetchClientPricingList();
  }, [fetchAllClients, fetchClientPricingList]);

  const handleSetOrUpdatePrice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClientId && !editingPricing) {
        toast({ title: "Please select a client.", variant: "destructive" });
        return;
    }
    if (parseFloat(price) < 0) {
        toast({ title: "Price cannot be negative.", variant: "destructive" });
        return;
    }

    setIsLoading(true);
    const token = localStorage.getItem("authToken");
    if (!token) { /* ... */ setIsLoading(false); return; }

    const clientIdToUse = editingPricing ? editingPricing.client_id : parseInt(selectedClientId);
    const method = editingPricing || clientPricingList.find(p => p.client_id === clientIdToUse) ? "PUT" : "POST";
    
    try {
      const response = await fetch(`/api/v1/admin/pricing/client/${clientIdToUse}`, {
        method: method,
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ price_per_message: price, currency, notes }),
      });
      const responseData = await response.json();
      if (response.ok) {
        toast({ title: responseData.message || "Pricing updated successfully!" });
        fetchClientPricingList(); // Refresh list
        // Reset form or close dialog
        setSelectedClientId("");
        setPrice("0.0100");
        setCurrency("USD");
        setNotes("");
        setEditingPricing(null);
        // Consider closing a dialog if this form is in one
        document.getElementById("closeDialogButton")?.click(); 
      } else {
        toast({ title: responseData.message || "Error updating pricing", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "Network Error (Updating Pricing)", variant: "destructive" });
    }
    setIsLoading(false);
  };

  const openEditDialog = (pricing: ClientPricingInfo) => {
    setEditingPricing(pricing);
    setSelectedClientId(String(pricing.client_id)); // Pre-select for clarity, though client_id is fixed
    setPrice(pricing.price_per_message);
    setCurrency(pricing.currency);
    setNotes(pricing.notes || "");
  };

  const handleDeletePricing = async (clientId: number) => {
    if (!confirm("Are you sure you want to delete pricing for this client? This might revert them to default pricing.")) return;
    setIsLoading(true);
    const token = localStorage.getItem("authToken");
    if (!token) { /* ... */ setIsLoading(true); return; }
    try {
        const response = await fetch(`/api/v1/admin/pricing/client/${clientId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` },
        });
        const data = await response.json();
        if (response.ok) {
            toast({ title: data.message || "Pricing deleted successfully!" });
            fetchClientPricingList();
        } else {
            toast({ title: data.message || "Error deleting pricing", variant: "destructive" });
        }
    } catch (error) {
        toast({ title: "Network Error (Deleting Pricing)", variant: "destructive" });
    }
    setIsLoading(false);
  };

  return (
    <div className="container mx-auto p-4 md:p-8 space-y-8">
      <h1 className="text-3xl font-bold mb-6">Manage Client Pricing</h1>

      <Dialog onOpenChange={(open) => { if (!open) { setEditingPricing(null); setSelectedClientId(""); setPrice("0.0100"); setCurrency("USD"); setNotes("");} }}>
        <DialogTrigger asChild>
          <Button>Set/Update Client Price</Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-[525px]">
          <DialogHeader>
            <DialogTitle>{editingPricing ? "Edit" : "Set New"} Client Pricing</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSetOrUpdatePrice} className="space-y-4 py-4">
            <div>
              <Label htmlFor="client">Client</Label>
              <Select 
                value={selectedClientId} 
                onValueChange={setSelectedClientId} 
                disabled={!!editingPricing} // Disable if editing existing
              >
                <SelectTrigger id="client">
                  <SelectValue placeholder="Select a client" />
                </SelectTrigger>
                <SelectContent>
                  {allClients.map(client => (
                    <SelectItem key={client.id} value={String(client.id)}>
                      {client.username} ({client.email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="price">Price Per Message</Label>
              <Input id="price" type="number" step="0.0001" value={price} onChange={(e) => setPrice(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="currency">Currency</Label>
              <Input id="currency" value={currency} onChange={(e) => setCurrency(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="notes">Notes (Optional)</Label>
              <Input id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
            </div>
            <DialogFooter>
                <DialogClose asChild>
                    <Button type="button" variant="outline" id="closeDialogButton">Cancel</Button>
                </DialogClose>
                <Button type="submit" disabled={isLoading}>{isLoading ? "Saving..." : "Save Pricing"}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Card>
        <CardHeader>
          <CardTitle>Current Client-Specific Pricing</CardTitle>
          <CardDescription>List of clients with custom pricing settings.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? <p>Loading pricing data...</p> : clientPricingList.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client Username</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Price/Message</TableHead>
                  <TableHead>Currency</TableHead>
                  <TableHead>Notes</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {clientPricingList.map((cp) => (
                  <TableRow key={cp.client_id}>
                    <TableCell>{cp.username}</TableCell>
                    <TableCell>{cp.email}</TableCell>
                    <TableCell>{cp.price_per_message}</TableCell>
                    <TableCell>{cp.currency}</TableCell>
                    <TableCell>{cp.notes || "-"}</TableCell>
                    <TableCell>{cp.updated_at ? new Date(cp.updated_at).toLocaleDateString() : "N/A"}</TableCell>
                    <TableCell className="space-x-2">
                        <DialogTrigger asChild>
                            <Button variant="outline" size="sm" onClick={() => openEditDialog(cp)}>Edit</Button>
                        </DialogTrigger>
                        <Button variant="destructive" size="sm" onClick={() => handleDeletePricing(cp.client_id)} disabled={isLoading}>
                            Delete
                        </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : <p>No client-specific pricing has been set up yet. All clients will use default pricing if applicable.</p>}
        </CardContent>
      </Card>
    </div>
  );
}

