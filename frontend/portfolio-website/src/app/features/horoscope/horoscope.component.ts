import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { HoroscopeService } from './services/horoscope.service';
import { HttpClientModule } from '@angular/common/http';
import { HoroscopeResponse } from './models/horoscope.model';

@Component({
  selector: 'app-horoscope',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HttpClientModule],
  templateUrl: './horoscope.component.html',
  providers: [HoroscopeService],
  styleUrls: ['./horoscope.component.scss']
})
export class HoroscopeComponent implements OnInit {
  horoscopeForm: FormGroup;
  horoscope: HoroscopeResponse | null = null;
  today = new Date();
  loading = false;
  error = '';

  languages = [
    { value: 'en', label: 'English' },
    { value: 'zh', label: '中文' }
  ];

  genders = [
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' }
  ];

  // Max date is today
  maxDate = new Date().toISOString().split('T')[0];

  constructor(
    private fb: FormBuilder,
    private horoscopeService: HoroscopeService
  ) {
    this.horoscopeForm = this.fb.group({
      birthdate: ['', Validators.required],
      gender: ['female', Validators.required],
      language: ['en', Validators.required]
    });
  }

  ngOnInit(): void {
  }

  onSubmit(): void {
    if (this.horoscopeForm.invalid) {
      return;
    }

    this.loading = true;
    this.error = '';
    this.horoscope = null;

    console.log('Get Horoscope form value:', this.horoscopeForm.value);

    this.horoscopeService.getHoroscopeByBirthdate(this.horoscopeForm.value)
      .subscribe({
        next: (response) => {
          console.log("Get response: ", response);
          this.horoscope = response;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to retrieve horoscope. Please try again.';
          console.error('Error fetching horoscope:', err);
          this.loading = false;
        }
      });
  }
}
