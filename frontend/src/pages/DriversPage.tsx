import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type { Driver, Shift, Order } from '../types'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog'
import { format, parseISO, startOfWeek, addDays, isSameDay } from 'date-fns'
import { Calendar } from 'lucide-react'

export default function DriversPage() {
  const [drivers, setDrivers] = useState<Driver[]>([])
  const [shifts, setShifts] = useState<Shift[]>([])
  const [selectedShift, setSelectedShift] = useState<Shift | null>(null)
  const [shiftOrders, setShiftOrders] = useState<Order[]>([])
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [driversData, shiftsData] = await Promise.all([
        api.getDrivers(),
        api.getShifts(),
      ])
      setDrivers(driversData)
      setShifts(shiftsData)
    } catch (err) {
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleShiftClick = async (shift: Shift) => {
    setSelectedShift(shift)
    setIsDialogOpen(true)
    
    // Load orders for this shift
    try {
      const allOrders = await api.getOrders(1, 1, 1000) // Get all orders
      const shiftDate = parseISO(shift.shift_date)
      const shiftStart = parseISO(`${shift.shift_date}T${shift.start_time}`)
      const shiftEnd = parseISO(`${shift.shift_date}T${shift.end_time}`)
      
      const ordersInShift = allOrders.filter((order) => {
        if (order.driver_id !== shift.driver_id) return false
        const orderPickup = parseISO(order.pickup_time)
        return (
          isSameDay(orderPickup, shiftDate) &&
          orderPickup >= shiftStart &&
          orderPickup <= shiftEnd
        )
      })
      
      setShiftOrders(ordersInShift)
    } catch (err) {
      console.error('Failed to load shift orders:', err)
      setShiftOrders([])
    }
  }

  const weekStart = startOfWeek(new Date(), { weekStartsOn: 1 })
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))

  const getShiftsForDay = (date: Date) => {
    return shifts.filter((shift) => {
      const shiftDate = parseISO(shift.shift_date)
      return isSameDay(shiftDate, date)
    })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Drivers</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-md border">
          <div className="p-4">
            <h2 className="mb-4 text-lg font-semibold">Driver List</h2>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Shifts</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center">
                      Loading...
                    </TableCell>
                  </TableRow>
                ) : drivers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center">
                      No drivers found
                    </TableCell>
                  </TableRow>
                ) : (
                  drivers.map((driver) => {
                    const driverShifts = shifts.filter(
                      (s) => s.driver_id === driver.id
                    )
                    return (
                      <TableRow key={driver.id}>
                        <TableCell>{driver.id}</TableCell>
                        <TableCell>{driver.name}</TableCell>
                        <TableCell>{driverShifts.length}</TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </div>

        <div className="rounded-md border">
          <div className="p-4">
            <h2 className="mb-4 text-lg font-semibold">Shift Calendar</h2>
            <div className="space-y-2">
              {weekDays.map((day) => {
                const dayShifts = getShiftsForDay(day)
                return (
                  <div
                    key={day.toISOString()}
                    className="rounded border p-2"
                  >
                    <div className="mb-2 text-sm font-medium">
                      {format(day, 'EEE, MMM dd')}
                    </div>
                    <div className="space-y-1">
                      {dayShifts.map((shift) => {
                        const driver = drivers.find(
                          (d) => d.id === shift.driver_id
                        )
                        return (
                          <button
                            key={shift.id}
                            onClick={() => handleShiftClick(shift)}
                            className="w-full rounded bg-blue-100 p-2 text-left text-sm hover:bg-blue-200"
                          >
                            <div className="font-medium">
                              {driver?.name || 'Unknown'}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {shift.start_time} - {shift.end_time}
                            </div>
                          </button>
                        )
                      })}
                      {dayShifts.length === 0 && (
                        <div className="text-sm text-muted-foreground">
                          No shifts
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Shift Details</DialogTitle>
            <DialogDescription>
              {selectedShift && (
                <>
                  {selectedShift.driver_name || 'Driver'} -{' '}
                  {format(parseISO(selectedShift.shift_date), 'MMM dd, yyyy')}{' '}
                  ({selectedShift.start_time} - {selectedShift.end_time})
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <h3 className="mb-2 font-semibold">Orders in this shift:</h3>
            {shiftOrders.length === 0 ? (
              <p className="text-sm text-muted-foreground">No orders</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Pickup Time</TableHead>
                    <TableHead>Weight</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {shiftOrders.map((order) => (
                    <TableRow key={order.order_id}>
                      <TableCell>{order.order_id}</TableCell>
                      <TableCell>{order.description || '-'}</TableCell>
                      <TableCell>
                        {format(
                          parseISO(order.pickup_time),
                          'HH:mm'
                        )}
                      </TableCell>
                      <TableCell>{order.weight} kg</TableCell>
                      <TableCell>{order.status}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

