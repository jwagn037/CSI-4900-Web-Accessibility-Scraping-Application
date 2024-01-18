import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UrlSubmissionFieldComponent } from './url-submission-field.component';

describe('UrlSubmissionFieldComponent', () => {
  let component: UrlSubmissionFieldComponent;
  let fixture: ComponentFixture<UrlSubmissionFieldComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UrlSubmissionFieldComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(UrlSubmissionFieldComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
