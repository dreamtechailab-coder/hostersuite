import { api } from './api'
import { resource } from './resource.service'
import type { Bed, Building, Floor, Property, Room } from '@/types'

export interface PropertyOverview {
  property: Property
  buildings: (Building & { floors: (Floor & { rooms: number; beds: number; occupied: number })[]; rooms: number; beds: number; occupied: number })[]
  beds: Record<string, number>
  active_tenants: number
}
export interface RoomDetails {
  room: Room
  building_name: string
  floor_name: string
  beds: Bed[]
  occupancies: { name: string; tenant: string; tenant_name: string; bed: string; status: string; check_in_date: string; check_out_date?: string; monthly_rent: number }[]
  meters: { name: string; meter_number: string; rate_per_unit: number; last_reading: number; last_reading_date?: string; is_active: 0 | 1 }[]
  readings: { name: string; reading_date: string; units_consumed: number; amount: number; billing_status: string }[]
}

export const propertyService = {
  list: (params = {}) => resource.list<Property>('PG Property', params),
  get: (name: string) => resource.get<Property>('PG Property', name),
  save: (data: Partial<Property>) => resource.save<Property>('PG Property', data),
  remove: (name: string) => resource.remove('PG Property', name),
  overview: (name: string) => api.pgGet<{ data: PropertyOverview }>('property.get_property_overview', { name }).then((r) => r.data),
  hierarchy: (property: string) =>
    api
      .pgGet<{ data: { buildings: { name: string; building_name: string }[]; floors: { name: string; building: string; floor_name: string }[] } }>(
        'property.get_hierarchy',
        { property },
      )
      .then((r) => r.data),
  saveBuilding: (data: Partial<Building>) => resource.save<Building>('PG Building', data),
  saveFloor: (data: Partial<Floor>) => resource.save<Floor>('PG Floor', data),
}

export const roomService = {
  list: (params = {}) => resource.list<Room>('PG Room', params),
  save: (data: Partial<Room>) => resource.save<Room>('PG Room', data),
  remove: (name: string) => resource.remove('PG Room', name),
  board: (params: { property?: string; building?: string; floor?: string; status?: string; search?: string; vacant_only?: number }) =>
    api.pgGet<{ data: Room[] }>('property.get_room_board', params).then((r) => r.data),
  details: (name: string) => api.pgGet<{ data: RoomDetails }>('property.get_room_details', { name }).then((r) => r.data),
  setBedStatus: (bed: string, status: 'Vacant' | 'Maintenance') => api.pgPost('property.set_bed_status', { bed, status }),
}
