#include "epd_w21.h"

void epd_spi_write(uint8_t data) {
    SPI.transfer(data);
}

void epd_write_cmd(uint8_t cmd) {
    digitalWrite(PIN_CS, LOW);
    digitalWrite(PIN_DC, LOW);
    epd_spi_write(cmd);
    digitalWrite(PIN_CS, HIGH);
}

void epd_write_data(uint8_t data) {
    digitalWrite(PIN_CS, LOW);
    digitalWrite(PIN_DC, HIGH);
    epd_spi_write(data);
    digitalWrite(PIN_CS, HIGH);
}

void epd_wait_busy() {
    unsigned long start = millis();
    while (digitalRead(PIN_BUSY) == 0) {
        delay(1);
        if (millis() - start > 5000) break;  // 5秒超时，防止卡死
    }
}

void epd_init() {
    delay(20);
    digitalWrite(PIN_RST, LOW);
    delay(40);
    digitalWrite(PIN_RST, HIGH);
    delay(50);
    epd_wait_busy();

    // BTST
    epd_write_cmd(0x06);
    epd_write_data(0x0F);
    epd_write_data(0x8B);
    epd_write_data(0x9C);
    epd_write_data(0x96);

    // PSR
    epd_write_cmd(0x00);
    epd_write_data(0x2F);
    epd_write_data(0x69);

    // PWR
    epd_write_cmd(0x01);
    epd_write_data(0x07);
    epd_write_data(0xF0);

    // CDI - border white
    epd_write_cmd(0x50);
    epd_write_data(0x37);

    // Resolution: 400x300
    epd_write_cmd(0x61);
    epd_write_data(EPD_W / 256);
    epd_write_data(EPD_W % 256);
    epd_write_data(EPD_H / 256);
    epd_write_data(EPD_H % 256);

    epd_write_cmd(0x62);
    epd_write_data(0x64);
    epd_write_data(0x53);

    epd_write_cmd(0x65);
    epd_write_data(0x00);
    epd_write_data(0x00);
    epd_write_data(0x00);
    epd_write_data(0x00);

    epd_write_cmd(0x30);
    epd_write_data(0x08);

    epd_write_cmd(0xE9);
    epd_write_data(0x01);

    epd_write_cmd(0x04);  // Power on
    epd_wait_busy();
}

void epd_sleep() {
    epd_write_cmd(0x02);   // Power off
    epd_write_data(0x00);
    epd_wait_busy();
    delay(100);

    epd_write_cmd(0x07);   // Deep sleep
    epd_write_data(0xA5);
}

void epd_refresh() {
    epd_write_cmd(0x12);   // Display Update
    epd_write_data(0x00);
    epd_wait_busy();
}

void epd_draw_raw(const uint8_t* buf) {
    epd_write_cmd(0x10);
    for (uint32_t i = 0; i < EPD_BYTES; i++) {
        epd_write_data(buf[i]);
        if (i % 1000 == 0) delay(1);  // 定期让出CPU
    }
    epd_refresh();
}
