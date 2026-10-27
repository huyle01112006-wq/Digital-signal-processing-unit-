`timescale 1ns / 1ps
// ============================================================================
// arty_top.v - Top cho board Arty Z7-20: chi 8 chan (clk, btn0, sw[1:0], led[3:0])
//  - Tu tao tin hieu thu 48 kHz = tong 3 song tam giac 100 Hz / 1 kHz / 8 kHz
//    (moi tan roi dung vao 1 dai Bass / Mid / Treble)
//  - sw[1:0] chon preset Gain:  00 phang | 01 tang bass | 10 tang treble | 11 chi mid
//  - led[3:0] = thanh muc do (peak) cua tin hieu ra
//  - btn0 = reset
// Dung de Implementation / tao bitstream; mo phong day du van dung audio_quality_tb.
// ============================================================================
module arty_top (
    input  wire       clk,       // 125 MHz
    input  wire       btn0,
    input  wire [1:0] sw,
    output wire [3:0] led
);
    // ---- reset: nut nhan (dong bo hoa) + power-on ----
    reg [2:0] btn_sync = 3'b000;
    reg [3:0] por      = 4'hF;
    always @(posedge clk) begin
        btn_sync <= {btn_sync[1:0], btn0};
        if (por != 0) por <= por - 1'b1;
    end
   // wire rst = btn_sync[2] | (por != 0);
reg rst_sync = 1'b1;
    always @(posedge clk) begin
        rst_sync <= btn_sync[2] | (por != 0);
    end
    // ---- xung lay mau 48 kHz: 125e6 / 2604 = 48.003 kHz ----
    localparam DIV = 2604;                      // >> N+3 = 258 chu ky cua bo loc
    reg [11:0] div  = 0;
    reg        tick = 0;
    always @(posedge clk) begin
        if (rst)                 begin div <= 0;        tick <= 0; end
        else if (div == DIV - 1) begin div <= 0;        tick <= 1; end
        else                     begin div <= div + 1;  tick <= 0; end
    end

    // ---- tin hieu thu: 3 song tam giac ----
    reg [15:0] ph_b = 0, ph_m = 0, ph_t = 0;
    always @(posedge clk) begin
        if (rst) begin ph_b <= 0; ph_m <= 0; ph_t <= 0; end
        else if (tick) begin
            ph_b <= ph_b + 16'd137;      // ~100  Hz
            ph_m <= ph_m + 16'd1365;     // ~1000 Hz
            ph_t <= ph_t + 16'd10923;    // ~8000 Hz
        end
    end

    function signed [15:0] tri_wave;          // +-16384
        input [15:0] p;
        reg   [14:0] m;
        begin
            m   = p[15] ? ~p[14:0] : p[14:0];
            tri_wave = $signed({1'b0, m}) - 16'sd16384;
        end
    endfunction

    wire signed [15:0] t_b = tri_wave(ph_b) >>> 2;
    wire signed [15:0] t_m = tri_wave(ph_m) >>> 2;
    wire signed [15:0] t_t = tri_wave(ph_t) >>> 2;
    wire signed [15:0] x   = t_b + t_m + t_t;          // toi da +-12288, khong bi clip

    // ---- preset Gain (Q8) ----
    reg signed [15:0] g_b, g_m, g_t;
    always @* begin
        case (sw)
            2'b00:   begin g_b = 16'sd256; g_m = 16'sd256; g_t = 16'sd256; end
            2'b01:   begin g_b = 16'sd512; g_m = 16'sd256; g_t = 16'sd128; end
            2'b10:   begin g_b = 16'sd128; g_m = 16'sd256; g_t = 16'sd512; end
            default: begin g_b = 16'sd0;   g_m = 16'sd256; g_t = 16'sd0;   end
        endcase
    end

    // ---- Equalizer ----
    wire signed [15:0] y;
    wire               y_valid;
    audio_equalizer_top #(.N(255)) u_eq (
        .clk(clk), .rst(rst), .in_valid(tick), .x_in(x),
        .gain_bass(g_b), .gain_mid(g_m), .gain_treble(g_t),
        .out_valid(y_valid), .out(y)
    );

    // ---- thanh muc do: peak co giam dan ----
    wire [15:0] ay = y[15] ? (~y + 16'd1) : y;
    reg  [15:0] peak = 0;
    always @(posedge clk) begin
        if (rst)          peak <= 0;
        else if (y_valid) peak <= (ay > peak) ? ay : (peak - (peak >> 7));
    end
  reg [3:0] led_reg = 0;
always @(posedge clk) begin
    if (rst) 
        led_reg <= 4'b0000;
    else 
        led_reg <= { peak > 16'd8192, peak > 16'd4096, peak > 16'd2048, peak > 16'd1024 };
end
assign led = led_reg;
endmodule