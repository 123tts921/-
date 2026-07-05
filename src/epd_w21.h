#ifndef EPD_W21_H
#define EPD_W21_H

#include <Arduino.h>
#include <SPI.h>

// Pin map for ESP32-C3
#define PIN_BUSY 10
#define PIN_RST  2
#define PIN_DC   1
#define PIN_CS   7
#define PIN_SCK  4
#define PIN_MOSI 6

// Display
#define EPD_W     400
#define EPD_H     300
#define EPD_BYTES (EPD_W * EPD_H / 4)  // 30000

// Color values (native: 00=black, 01=white, 10=yellow, 11=red)
#define EPD_BLACK  0x00
#define EPD_WHITE  0x01
#define EPD_YELLOW 0x02
#define EPD_RED    0x03

void epd_spi_write(uint8_t data);
void epd_write_cmd(uint8_t cmd);
void epd_write_data(uint8_t data);
void epd_wait_busy();
void epd_init();
void epd_sleep();
void epd_refresh();
void epd_draw_raw(const uint8_t* buf);

#endif
