// frontend/src/app/dashboard/reports/page.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { DateRangePicker } from "@/components/ui/date-range-picker"; // Assuming this component exists
import { useToast } from "@/hooks/use-toast";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell } from "recharts";
import { DateRange } from "react-day-picker";
import { subDays, format, parseISO } from "date-fns";

interface FinancialSummary {
  start_date: string;
  end_date: string;
  total_top_ups: number;
  total_deductions: number;
  net_wallet_change: number;
  avg_cost_per_message: number;
  daily_profit_placeholder: number;
  current_wallet_balance: number;
  currency: string;
  total_messages_sent_in_period: number;
}

interface CampaignPerformance {
  campaign_id: number;
  campaign_name: string;
  campaign_status: string;
  total_recipients: number;
  total_messages_attempted: number;
  messages_successfully_sent: number;
  messages_delivered: number;
  messages_read: number;
  messages_failed: number;
  sent_rate_percentage: number;
  delivery_rate_percentage: number;
  read_rate_percentage: number;
  failure_rate_percentage: number;
}

interface DailyTransactionSummary {
    date: string;
    total_top_ups_today: number;
    total_deductions_today: number;
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8"];

export default function ReportsPage() {
  const [financialSummary, setFinancialSummary] = useState<FinancialSummary | null>(null);
  const [campaignPerformance, setCampaignPerformance] = useState<CampaignPerformance[]>([]);
  const [dailyTransactions, setDailyTransactions] = useState<DailyTransactionSummary | null>(null);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>("all");
  const [campaignsForSelect, setCampaignsForSelect] = useState<{id: number, campaign_name: string}[]>([]);

  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: subDays(new Date(), 29),
    to: new Date(),
  });
  const [isLoadingFinancial, setIsLoadingFinancial] = useState(false);
  const [isLoadingCampaign, setIsLoadingCampaign] = useState(false);
  const [isLoadingDaily, setIsLoadingDaily] = useState(false);
  const { toast } = useToast();

  const fetchFinancialSummary = useCallback(async (currentDateRange?: DateRange) => {
    const rangeToUse = currentDateRange || dateRange;
    if (!rangeToUse?.from || !rangeToUse?.to) return;
    setIsLoadingFinancial(true);
    const token = localStorage.getItem("authToken");
    if (!token) { /* ... */ setIsLoadingFinancial(false); return; }
    try {
      const response = await fetch(`/api/v1/reports/financial-summary?start_date=${format(rangeToUse.from, "yyyy-MM-dd")}&end_date=${format(rangeToUse.to, "yyyy-MM-dd")}`, {
        headers: { "Authorization": `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setFinancialSummary(data);
      } else {
        toast({ title: "Error fetching financial summary", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "Network Error (Financial)", variant: "destructive" });
    }
    setIsLoadingFinancial(false);
  }, [toast, dateRange]);

  const fetchCampaignPerformance = useCallback(async (campaignId?: string) => {
    setIsLoadingCampaign(true);
    const token = localStorage.getItem("authToken");
    if (!token) { /* ... */ setIsLoadingCampaign(false); return; }
    const campId = (campaignId === undefined) ? selectedCampaignId : campaignId;
    const url = campId === "all" ? "/api/v1/reports/campaign-performance" : `/api/v1/reports/campaign-performance?campaign_id=${campId}`;
    try {
      const response = await fetch(url, { headers: { "Authorization": `Bearer ${token}` } });
      if (response.ok) {
        const data = await response.json();
        setCampaignPerformance(data);
      } else {
        toast({ title: "Error fetching campaign performance", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "Network Error (Campaign)", variant: "destructive" });
    }
    setIsLoadingCampaign(false);
  }, [toast, selectedCampaignId]);

  const fetchDailyTransactions = useCallback(async () => {
    setIsLoadingDaily(true);
    const token = localStorage.getItem("authToken");
    if (!token) { /* ... */ setIsLoadingDaily(false); return; }
    try {
        const response = await fetch(`/api/v1/reports/daily-transactions?date=${format(new Date(), "yyyy-MM-dd")}`, {
            headers: { "Authorization": `Bearer ${token}` },
        });
        if(response.ok) {
            const data = await response.json();
            setDailyTransactions(data);
        } else {
            toast({ title: "Error fetching daily transactions", variant: "destructive" });
        }
    } catch (error) {
        toast({ title: "Network Error (Daily Transactions)", variant: "destructive" });
    }
    setIsLoadingDaily(false);
  }, [toast]);

  const fetchCampaignListForSelect = useCallback(async () => {
    const token = localStorage.getItem("authToken");
    if (!token) return;
    try {
        const response = await fetch("/api/v1/campaigns", { headers: { "Authorization": `Bearer ${token}` } });
        if (response.ok) {
            const data = await response.json();
            setCampaignsForSelect(data.map((c: any) => ({id: c.id, campaign_name: c.campaign_name })));
        }
    } catch (error) {
        console.error("Failed to fetch campaign list for select");
    }
  }, []);

  useEffect(() => {
    fetchFinancialSummary();
    fetchCampaignPerformance();
    fetchDailyTransactions();
    fetchCampaignListForSelect();
  }, [fetchFinancialSummary, fetchCampaignPerformance, fetchDailyTransactions, fetchCampaignListForSelect]);
  
  const handleDateRangeChange = (newRange: DateRange | undefined) => {
    setDateRange(newRange);
    if (newRange) fetchFinancialSummary(newRange);
  }

  const campaignChartData = campaignPerformance.map(cp => ({
    name: cp.campaign_name.substring(0, 15) + (cp.campaign_name.length > 15 ? "..." : ""), // Shorten name for chart
    Sent: cp.messages_successfully_sent,
    Delivered: cp.messages_delivered,
    Read: cp.messages_read,
    Failed: cp.messages_failed,
  }));

  const overallCampaignStats = campaignPerformance.reduce((acc, cur) => {
    acc.total_attempted += cur.total_messages_attempted;
    acc.total_sent += cur.messages_successfully_sent;
    acc.total_delivered += cur.messages_delivered;
    acc.total_read += cur.messages_read;
    acc.total_failed += cur.messages_failed;
    return acc;
  }, { total_attempted: 0, total_sent: 0, total_delivered: 0, total_read: 0, total_failed: 0 });

  const pieData = [
    { name: "Sent", value: overallCampaignStats.total_sent },
    { name: "Delivered", value: overallCampaignStats.total_delivered },
    { name: "Read", value: overallCampaignStats.total_read },
    { name: "Failed", value: overallCampaignStats.total_failed },
  ].filter(d => d.value > 0);

  return (
    <div className="container mx-auto p-4 md:p-8 space-y-8">
      <h1 className="text-3xl font-bold mb-6">Reports Dashboard</h1>

      {/* Financial Summary Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Financial Summary</CardTitle>
            <CardDescription>
              Overview of your financial transactions from {dateRange?.from ? format(dateRange.from, "LLL dd, y") : ""} to {dateRange?.to ? format(dateRange.to, "LLL dd, y") : ""}
            </CardDescription>
          </div>
          <DateRangePicker date={dateRange} onDateChange={handleDateRangeChange} />
        </CardHeader>
        <CardContent>
          {isLoadingFinancial ? <p>Loading financial data...</p> : financialSummary ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
              <InfoBox title="Current Wallet Balance" value={`${financialSummary.currency} ${financialSummary.current_wallet_balance.toFixed(2)}`} />
              <InfoBox title="Total Top-ups (Period)" value={`${financialSummary.currency} ${financialSummary.total_top_ups.toFixed(2)}`} />
              <InfoBox title="Total Deductions (Period)" value={`${financialSummary.currency} ${financialSummary.total_deductions.toFixed(2)}`} />
              <InfoBox title="Net Wallet Change (Period)" value={`${financialSummary.currency} ${financialSummary.net_wallet_change.toFixed(2)}`} className={financialSummary.net_wallet_change >= 0 ? "text-green-600" : "text-red-600"} />
              <InfoBox title="Avg. Cost Per Message (Period)" value={`${financialSummary.currency} ${financialSummary.avg_cost_per_message.toFixed(4)}`} />
              <InfoBox title="Total Messages Sent (Period)" value={financialSummary.total_messages_sent_in_period.toString()} />
              {dailyTransactions && (
                <>
                    <InfoBox title="Top-ups (Today)" value={`${financialSummary.currency} ${dailyTransactions.total_top_ups_today.toFixed(2)}`} />
                    <InfoBox title="Deductions (Today)" value={`${financialSummary.currency} ${dailyTransactions.total_deductions_today.toFixed(2)}`} />
                </>
              )}
            </div>
          ) : <p>No financial data available for the selected period.</p>}
        </CardContent>
      </Card>

      {/* Campaign Performance Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
            <div>
                <CardTitle>Campaign Performance</CardTitle>
                <CardDescription>Effectiveness of your messaging campaigns.</CardDescription>
            </div>
            <div className="w-64">
                <Select value={selectedCampaignId} onValueChange={(value) => {setSelectedCampaignId(value); fetchCampaignPerformance(value);}}>
                    <SelectTrigger><SelectValue placeholder="Select Campaign" /></SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Campaigns</SelectItem>
                        {campaignsForSelect.map(c => (
                            <SelectItem key={c.id} value={String(c.id)}>{c.campaign_name}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>
        </CardHeader>
        <CardContent>
          {isLoadingCampaign ? <p>Loading campaign data...</p> : campaignPerformance.length > 0 ? (
            <div className="space-y-6">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={campaignChartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Sent" fill="#8884d8" />
                  <Bar dataKey="Delivered" fill="#82ca9d" />
                  <Bar dataKey="Read" fill="#ffc658" />
                  <Bar dataKey="Failed" fill="#ff8042" />
                </BarChart>
              </ResponsiveContainer>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Campaign Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Recipients</TableHead>
                    <TableHead>Attempted</TableHead>
                    <TableHead>Sent (%)</TableHead>
                    <TableHead>Delivered (%)</TableHead>
                    <TableHead>Read (%)</TableHead>
                    <TableHead>Failed (%)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {campaignPerformance.map((cp) => (
                    <TableRow key={cp.campaign_id}>
                      <TableCell className="font-medium">{cp.campaign_name}</TableCell>
                      <TableCell>{cp.campaign_status}</TableCell>
                      <TableCell>{cp.total_recipients}</TableCell>
                      <TableCell>{cp.total_messages_attempted}</TableCell>
                      <TableCell>{cp.messages_successfully_sent} ({cp.sent_rate_percentage}%)</TableCell>
                      <TableCell>{cp.messages_delivered} ({cp.delivery_rate_percentage}%)</TableCell>
                      <TableCell>{cp.messages_read} ({cp.read_rate_percentage}%)</TableCell>
                      <TableCell>{cp.messages_failed} ({cp.failure_rate_percentage}%)</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {selectedCampaignId === "all" && pieData.length > 0 && (
                <Card className="mt-6">
                    <CardHeader><CardTitle>Overall Message Status Distribution</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                                    {pieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
              )}
            </div>
          ) : <p>No campaign data available.</p>}
        </CardContent>
      </Card>
    </div>
  );
}

interface InfoBoxProps {
  title: string;
  value: string;
  className?: string;
}

const InfoBox: React.FC<InfoBoxProps> = ({ title, value, className }) => (
  <div className={`p-4 bg-gray-50 dark:bg-gray-800 rounded-lg shadow ${className}`}>
    <h3 className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{title}</h3>
    <p className="text-xl font-semibold text-gray-900 dark:text-white">{value}</p>
  </div>
);

// Make sure to create the DatePickerWithRange component or use an existing one from shadcn/ui if available.
// Example placeholder for DatePickerWithRange if not already part of your components:
// src/components/ui/date-range-picker.tsx
/*
"use client"

import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon } from "lucide-react"
import { DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DatePickerWithRangeProps extends React.HTMLAttributes<HTMLDivElement> {
  date: DateRange | undefined;
  onDateChange: (date: DateRange | undefined) => void;
}

export function DatePickerWithRange({
  className,
  date,
  onDateChange
}: DatePickerWithRangeProps) {
  return (
    <div className={cn("grid gap-2", className)}>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            id="date"
            variant={"outline"}
            className={cn(
              "w-[300px] justify-start text-left font-normal",
              !date && "text-muted-foreground"
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date?.from ? (
              date.to ? (
                <>
                  {format(date.from, "LLL dd, y")} -{" "}
                  {format(date.to, "LLL dd, y")}
                </>
              ) : (
                format(date.from, "LLL dd, y")
              )
            ) : (
              <span>Pick a date range</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="end">
          <Calendar
            initialFocus
            mode="range"
            defaultMonth={date?.from}
            selected={date}
            onSelect={onDateChange}
            numberOfMonths={2}
          />
        </PopoverContent>
      </Popover>
    </div>
  )
}
*/

