import { Component, Input } from '@angular/core';

/**
 * Stand-in for every screen not yet built. Routed to from feature route files so the
 * sidebar and routing tree are real end-to-end even before a module's milestone lands
 * (plan §9) -- e.g. Units/Buildings/Reservations land in later milestones, this is what
 * they point at until then. Styled as a real empty-state, not a dashed debug box, so a
 * scaffolded screen reads as "not built yet" rather than "broken".
 */
@Component({
  selector: 'app-placeholder',
  standalone: true,
  template: `
    <div class="empty-state">
      <div class="empty-state__icon"><i class="pi pi-hammer"></i></div>
      <h2 class="empty-state__title">{{ title }}</h2>
      <p class="empty-state__note">
        {{ note || 'Not built yet. This screen (and its backend API) lands in a later milestone -- see the build plan for the delivery order.' }}
      </p>
    </div>
  `,
  styles: [
    `
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
        max-width: 34rem;
        margin: 2rem auto;
        padding: 2.5rem;
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        text-align: left;
      }
      .empty-state__icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 2.75rem;
        height: 2.75rem;
        border-radius: 10px;
        background: #f1f5f9;
        color: #64748b;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
      }
      .empty-state__title {
        margin: 0;
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
      }
      .empty-state__note {
        margin: 0;
        color: #64748b;
        line-height: 1.5;
      }
    `,
  ],
})
export class PlaceholderComponent {
  @Input() title = '';
  @Input() note = '';
}
