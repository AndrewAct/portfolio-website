import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HoroscopeComponent } from './horoscope.component';

describe('HoroscopeComponent', () => {
  let component: HoroscopeComponent;
  let fixture: ComponentFixture<HoroscopeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HoroscopeComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HoroscopeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
