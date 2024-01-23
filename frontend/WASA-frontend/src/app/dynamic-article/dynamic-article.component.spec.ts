import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DynamicArticleComponent } from './dynamic-article.component';

describe('DynamicArticleComponent', () => {
  let component: DynamicArticleComponent;
  let fixture: ComponentFixture<DynamicArticleComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DynamicArticleComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(DynamicArticleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
