import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RoomCard from '../components/dashboard/RoomCard.vue'
import type { Room } from '../api'

function makeRoom(overrides: Partial<Room> = {}): Room {
  return {
    id: 1,
    name: 'Zimmer 1',
    subnet: '10.3.18.0/24',
    vlan_id: 18,
    internet_enabled: true,
    schedule_enabled: false,
    schedule_open_time: null,
    schedule_lock_time: null,
    manual_override_active: false,
    manual_override_enabled: null,
    control_mode: 'manual',
    schedule_target_enabled: null,
    ...overrides,
  }
}

describe('RoomCard', () => {
  it('zeigt status-on wenn internet_enabled=true', () => {
    const wrapper = mount(RoomCard, {
      props: { room: makeRoom({ internet_enabled: true }), loading: false },
    })
    expect(wrapper.find('.status-on').exists()).toBe(true)
    expect(wrapper.find('.status-off').exists()).toBe(false)
  })

  it('zeigt status-off wenn internet_enabled=false', () => {
    const wrapper = mount(RoomCard, {
      props: { room: makeRoom({ internet_enabled: false }), loading: false },
    })
    expect(wrapper.find('.status-off').exists()).toBe(true)
    expect(wrapper.find('.status-on').exists()).toBe(false)
  })

  it('zeigt Override-Badge nur wenn manual_override_active=true', () => {
    const withOverride = mount(RoomCard, {
      props: {
        room: makeRoom({ manual_override_active: true, manual_override_enabled: true }),
        loading: false,
      },
    })
    expect(withOverride.find('.meta-override').exists()).toBe(true)

    const withoutOverride = mount(RoomCard, {
      props: { room: makeRoom({ manual_override_active: false }), loading: false },
    })
    expect(withoutOverride.find('.meta-override').exists()).toBe(false)
  })

  it('zeigt Schedule-Badge nur wenn schedule_enabled=true', () => {
    const withSchedule = mount(RoomCard, {
      props: {
        room: makeRoom({
          schedule_enabled: true,
          schedule_open_time: '08:00',
          schedule_lock_time: '17:00',
        }),
        loading: false,
      },
    })
    expect(withSchedule.find('.meta-schedule').exists()).toBe(true)

    const withoutSchedule = mount(RoomCard, {
      props: { room: makeRoom({ schedule_enabled: false }), loading: false },
    })
    expect(withoutSchedule.find('.meta-schedule').exists()).toBe(false)
  })

  it('zeigt VLAN-ID korrekt an', () => {
    const wrapper = mount(RoomCard, {
      props: { room: makeRoom({ vlan_id: 22 }), loading: false },
    })
    expect(wrapper.find('.vlan-badge').text()).toContain('22')
  })

  it('deaktiviert Buttons wenn loading=true', () => {
    const wrapper = mount(RoomCard, {
      props: { room: makeRoom(), loading: true },
    })
    const buttons = wrapper.findAll('button')
    buttons.forEach(btn => {
      expect(btn.attributes('disabled')).toBeDefined()
    })
  })
})
