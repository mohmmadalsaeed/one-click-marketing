// frontend/src/app/dashboard/pricing/page.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface ClientPricingDetails {
  price_per_message: string;
  currency: string;
  // Potentially add other pricing details here if the model expands
  // e.g., price_per_text_message, price_per_media_message, etc.
  notes?: string; // Admin notes, probably not shown to client but fetched for completeness
  updated_at?: string;
}

export default function ClientPricingPage() {
  const [pricingDetails, setPricingDetails] = useState<ClientPricingDetails | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const fetchPricingDetails = useCallback(async () => {
    setIsLoading(true);
    const token = localStorage.getItem("authToken");
    if (!token) {
      toast({ title: "Authentication Error", description: "No auth token found. Please log in again.", variant: "destructive" });
      setIsLoading(false);
      return;
    }

    try {
      // This endpoint needs to be created in the backend for clients to fetch their own pricing.
      // It should be different from the admin one.
      // Let's assume an endpoint like /api/v1/client/my-pricing
      const response = await fetch("/api/v1/client/my-pricing", { // NEW ENDPOINT TO BE CREATED
        headers: { "Authorization": `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setPricingDetails(data);
      } else if (response.status === 404) {
        // If 404, it means no specific pricing is set, so we can show a default or a message.
        // For now, we can assume a default pricing might be communicated or handled differently.
        // Or, the backend could return a default pricing structure if no specific one is set.
        setPricingDetails(null); // Or set to a default structure
        toast({ title: "No Specific Pricing Set", description: "You are currently on standard pricing.", variant: "info" });
      } else {
        const errorData = await response.json();
        toast({ title: "Error Fetching Pricing", description: errorData.message || "Could not retrieve your pricing details.", variant: "destructive" });
      }
    } catch (error) {
      console.error("Fetch pricing error:", error);
      toast({ title: "Network Error", description: "Failed to connect to the server to get pricing details.", variant: "destructive" });
    }
    setIsLoading(false);
  }, [toast]);

  useEffect(() => {
    fetchPricingDetails();
  }, [fetchPricingDetails]);

  return (
    <div className="container mx-auto p-4 md:p-8 space-y-8">
      <h1 className="text-3xl font-bold mb-6">Your Messaging Pricing</h1>

      <Card>
        <CardHeader>
          <CardTitle>Current Pricing Plan</CardTitle>
          <CardDescription>
            Details of the pricing applied to your account for sending messages.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p>Loading your pricing details...</p>
          ) : pricingDetails ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Item</TableHead>
                  <TableHead>Rate</TableHead>
                  <TableHead>Currency</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow>
                  <TableCell className="font-medium">Price Per Message</TableCell>
                  <TableCell>{pricingDetails.price_per_message}</TableCell>
                  <TableCell>{pricingDetails.currency}</TableCell>
                </TableRow>
                {/* Add more rows here if the pricing model becomes more complex */}
                {/* e.g., different rates for different message types */}
              </TableBody>
            </Table>
          ) : (
            <p>Your account is currently on standard platform pricing. If you have questions, please contact support.</p>
          )}
          {pricingDetails?.updated_at && (
            <p className="text-xs text-muted-foreground mt-4">
              Pricing last updated: {new Date(pricingDetails.updated_at).toLocaleDateString()}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
            <CardTitle>Understanding Your Bill</CardTitle>
            <CardDescription>Costs are deducted from your wallet balance based on the number of messages sent according to the rates above. You can view your transaction history in the Financial Reports section.</CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}

