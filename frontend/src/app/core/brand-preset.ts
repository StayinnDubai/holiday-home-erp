import { definePreset } from '@primeng/themes';
import Aura from '@primeng/themes/aura';
import { BRASS, STONE } from './design-tokens';

/**
 * Overrides PrimeNG's stock Aura preset (default: emerald primary, slate neutrals --
 * confirmed by inspecting node_modules/@primeng/themes/aura/base -- with zero brand
 * connection) with the brass/stone palette from design-tokens.ts. `definePreset` deep-
 * merges this object onto Aura, so every token we don't touch keeps Aura's sensible
 * default shape (spacing, transitions, per-component structure) -- only color and radius
 * primitives change.
 *
 * Because most of Aura's ~90 component token files reference `{primary.X}` / `{surface.X}`
 * by name rather than hard-coding colors, overriding just these two ramps re-skins every
 * PrimeNG component (buttons, dialogs, dropdowns, tabs, confirm dialog, form fields) in
 * one place -- see the design-audit for why that's the highest-leverage single change.
 */
export const brandPreset = definePreset(Aura, {
  primitive: {
    brass: BRASS,
    stone: STONE,
    borderRadius: {
      sm: '6px',
      md: '10px',
      lg: '14px',
      xl: '14px',
    },
  },
  semantic: {
    primary: {
      50: '{brass.50}',
      100: '{brass.100}',
      200: '{brass.200}',
      300: '{brass.300}',
      400: '{brass.400}',
      500: '{brass.500}',
      600: '{brass.600}',
      700: '{brass.700}',
      800: '{brass.800}',
      900: '{brass.900}',
      950: '{brass.950}',
    },
    colorScheme: {
      light: {
        surface: {
          0: '#FFFDFB',
          50: '{stone.50}',
          100: '{stone.100}',
          200: '{stone.200}',
          300: '{stone.300}',
          400: '{stone.400}',
          500: '{stone.500}',
          600: '{stone.600}',
          700: '{stone.700}',
          800: '{stone.800}',
          900: '{stone.900}',
          950: '{stone.950}',
        },
        text: {
          // Aura's default is `{surface.700}` (a mid-tone) -- explicit ink here instead,
          // since the brief calls for near-black primary text matching the wordmark.
          color: '#1C1917',
          hoverColor: '{stone.950}',
        },
      },
    },
  },
});
