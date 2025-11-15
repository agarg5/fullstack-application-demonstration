export interface Merchant {
  id: number
  name: string
  email: string
}

export interface Driver {
  id: number
  name: string
  shifts?: Shift[]
}

export interface Shift {
  id: number
  driver_id: number
  shift_date: string
  start_time: string
  end_time: string
  driver_name?: string
}

export interface Vehicle {
  id: number
  driver_id: number
  max_orders: number
  max_weight: number
  driver_name?: string
}

export interface Order {
  order_id: number
  merchant_id: number
  driver_id?: number
  vehicle_id?: number
  status: 'pending' | 'assigned' | 'completed' | 'cancelled'
  description?: string
  pickup_time: string
  dropoff_time: string
  weight: number
  driver?: {
    id: number
    name: string
  }
  merchant_name?: string
  merchant_email?: string
}

export interface LocationUpdate {
  driver_id: number
  driver_name: string
  latitude: number
  longitude: number
  timestamp: string
}

