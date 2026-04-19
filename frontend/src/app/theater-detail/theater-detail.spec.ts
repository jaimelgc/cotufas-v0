import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TheaterDetail } from './theater-detail';

describe('TheaterDetail', () => {
  let component: TheaterDetail;
  let fixture: ComponentFixture<TheaterDetail>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TheaterDetail],
    }).compileComponents();

    fixture = TestBed.createComponent(TheaterDetail);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
