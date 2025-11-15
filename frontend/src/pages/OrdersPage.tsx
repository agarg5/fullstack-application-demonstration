import { useState, useEffect } from "react";
import ReactPaginate from "react-paginate";
import { api } from "../api/client";
import type { Order, Merchant } from "../types";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Plus, Edit, X, Search } from "lucide-react";
import { format } from "date-fns";

const STATUS_COLORS = {
  pending: "bg-yellow-100 text-yellow-800",
  assigned: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [selectedMerchant, setSelectedMerchant] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    description: "",
    pickup_time: "",
    dropoff_time: "",
    weight: "",
  });

  useEffect(() => {
    loadMerchants();
  }, []);

  // Debounce search term to avoid too many API calls
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 500); // 500ms delay

    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    if (selectedMerchant) {
      setPage(1); // Reset to page 1 when merchant or search changes
    }
  }, [selectedMerchant, debouncedSearchTerm]);

  useEffect(() => {
    if (selectedMerchant) {
      loadOrders();
    }
  }, [selectedMerchant, page, debouncedSearchTerm]);

  const loadMerchants = async () => {
    try {
      const data = await api.getMerchants();
      setMerchants(data);
      if (data.length > 0 && !selectedMerchant) {
        setSelectedMerchant(data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load merchants");
    }
  };

  const loadOrders = async () => {
    if (!selectedMerchant) return;
    setLoading(true);
    try {
      // Only send search if there's a search term
      const searchQuery = debouncedSearchTerm.trim() || undefined;
      const response = await api.getOrders(
        selectedMerchant,
        page,
        perPage,
        searchQuery
      );
      setOrders(response.orders);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load orders");
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = ({ selected }: { selected: number }) => {
    setPage(selected + 1); // react-paginate uses 0-based index, our API uses 1-based
  };

  const handleCreate = () => {
    setEditingOrder(null);
    setFormData({
      description: "",
      pickup_time: "",
      dropoff_time: "",
      weight: "",
    });
    setIsDialogOpen(true);
  };

  const handleEdit = (order: Order) => {
    setEditingOrder(order);
    setFormData({
      description: order.description || "",
      pickup_time: order.pickup_time.slice(0, 16),
      dropoff_time: order.dropoff_time.slice(0, 16),
      weight: order.weight.toString(),
    });
    setIsDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!selectedMerchant) return;

    setError(null);
    setSuccess(null);

    try {
      if (editingOrder) {
        await api.updateOrder(editingOrder.order_id, {
          merchant_id: selectedMerchant,
          ...formData,
          weight: parseFloat(formData.weight),
        });
        setSuccess("Order updated successfully");
      } else {
        await api.createOrder({
          merchant_id: selectedMerchant,
          ...formData,
          weight: parseFloat(formData.weight),
        });
        setSuccess("Order created successfully");
      }
      setIsDialogOpen(false);
      // Reset to page 1 to see the new/updated order
      setPage(1);
      // Explicitly reload orders so changes are visible immediately
      await loadOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save order");
    }
  };

  const handleCancel = async (orderId: number) => {
    if (!confirm("Are you sure you want to cancel this order?")) return;

    try {
      await api.cancelOrder(orderId);
      setSuccess("Order cancelled successfully");
      loadOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to cancel order");
    }
  };

  // Filter orders by status only (search is now handled by the API)
  const filteredOrders = orders.filter((order) => {
    if (statusFilter !== "all" && order.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Orders</h1>
        <div className="flex items-center gap-4">
          <Select
            value={selectedMerchant?.toString() || ""}
            onValueChange={(value) => setSelectedMerchant(parseInt(value))}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select merchant" />
            </SelectTrigger>
            <SelectContent>
              {merchants.map((merchant) => (
                <SelectItem key={merchant.id} value={merchant.id.toString()}>
                  {merchant.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={handleCreate}>
            <Plus className="mr-2 h-4 w-4" />
            Create Order
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4 text-red-800">{error}</div>
      )}
      {success && (
        <div className="rounded-md bg-green-50 p-4 text-green-800">
          {success}
        </div>
      )}

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search orders..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="assigned">Assigned</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Pickup Time</TableHead>
              <TableHead>Dropoff Time</TableHead>
              <TableHead>Weight</TableHead>
              <TableHead>Driver</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : filteredOrders.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center">
                  No orders found
                </TableCell>
              </TableRow>
            ) : (
              filteredOrders.map((order) => (
                <TableRow key={order.order_id}>
                  <TableCell>{order.order_id}</TableCell>
                  <TableCell>{order.description || "-"}</TableCell>
                  <TableCell>
                    {format(new Date(order.pickup_time), "MMM dd, yyyy HH:mm")}
                  </TableCell>
                  <TableCell>
                    {format(new Date(order.dropoff_time), "MMM dd, yyyy HH:mm")}
                  </TableCell>
                  <TableCell>{order.weight} kg</TableCell>
                  <TableCell>
                    {order.driver ? order.driver.name : "-"}
                  </TableCell>
                  <TableCell>
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${
                        STATUS_COLORS[order.status]
                      }`}
                    >
                      {order.status}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(order)}
                        disabled={
                          order.status === "completed" ||
                          order.status === "cancelled"
                        }
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleCancel(order.order_id)}
                        disabled={
                          order.status === "completed" ||
                          order.status === "cancelled"
                        }
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between py-4">
          <div className="text-sm text-muted-foreground">
            Showing {(page - 1) * perPage + 1} to{" "}
            {Math.min(page * perPage, total)} of {total} orders
          </div>
          <ReactPaginate
            previousLabel="Previous"
            nextLabel="Next"
            pageCount={totalPages}
            onPageChange={handlePageChange}
            forcePage={page - 1} // Convert to 0-based index
            containerClassName="flex items-center gap-1"
            previousClassName=""
            nextClassName=""
            pageClassName=""
            breakClassName=""
            previousLinkClassName="px-3 py-2 text-sm font-medium text-foreground bg-background border border-input rounded-md hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-background"
            nextLinkClassName="px-3 py-2 text-sm font-medium text-foreground bg-background border border-input rounded-md hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-background"
            pageLinkClassName="px-3 py-2 text-sm font-medium text-foreground bg-background border border-input rounded-md hover:bg-accent hover:text-accent-foreground min-w-[40px] text-center"
            activeLinkClassName="px-3 py-2 text-sm font-medium text-primary-foreground bg-primary border border-primary rounded-md hover:bg-primary/90 min-w-[40px] text-center"
            disabledLinkClassName="opacity-50 cursor-not-allowed"
            breakLabel="..."
            breakLinkClassName="px-3 py-2 text-sm text-muted-foreground"
            marginPagesDisplayed={1}
            pageRangeDisplayed={5}
          />
        </div>
      )}

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {editingOrder ? "Edit Order" : "Create Order"}
            </DialogTitle>
            <DialogDescription>
              {editingOrder
                ? "Update the order details below."
                : "Fill in the details to create a new order."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <label className="text-sm font-medium">Description</label>
              <Input
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Order description"
              />
            </div>
            <div className="grid gap-2">
              <label className="text-sm font-medium">Pickup Time</label>
              <Input
                type="datetime-local"
                value={formData.pickup_time}
                onChange={(e) =>
                  setFormData({ ...formData, pickup_time: e.target.value })
                }
              />
            </div>
            <div className="grid gap-2">
              <label className="text-sm font-medium">Dropoff Time</label>
              <Input
                type="datetime-local"
                value={formData.dropoff_time}
                onChange={(e) =>
                  setFormData({ ...formData, dropoff_time: e.target.value })
                }
              />
            </div>
            <div className="grid gap-2">
              <label className="text-sm font-medium">Weight (kg)</label>
              <Input
                type="number"
                step="0.01"
                value={formData.weight}
                onChange={(e) =>
                  setFormData({ ...formData, weight: e.target.value })
                }
                placeholder="0.00"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
