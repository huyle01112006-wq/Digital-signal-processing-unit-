`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 27.10.2026 12:34:51
// Design Name: 
// Module Name: audio_quality_tb
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module audio_quality_tb();
parameter NUM_SAMPLE = 144000 ; // compare in 3 second with 48 kHz
parameter CLK_E = 300 ; // bass delay N+1 , mid 1, treble 1 = N += 3 with N = 255
parameter IN_FILE  = "input_audio.mem";
parameter OUT_FILE= "out_testbench.mem" ;
parameter GOLDEN_FILE= "golden_output.mem" ;
parameter CHECK_GOLDEN = 1;

localparam signed [15:0] GAIN_BASS = 16'sd512; 
localparam signed [15:0] GAIN_MID = 16'sd256 ;
localparam signed [15:0] GAIN_TREBLE = 16'sd128 ; 

reg clk = 1'b0 ; 
reg rst = 1'b1 ;
reg in_valid = 1'b0 ; 
reg signed [15:0] x_in = 16'sd0 ;
wire out_valid ;
wire signed [15:0] out; 
always #10 clk = ~clk;

audio_equalizer_top dut(
.clk(clk), .rst(rst),.in_valid(in_valid), .x_in(x_in), .out_valid(out_valid), .out(out),
.gain_bass(GAIN_BASS),.gain_mid(GAIN_MID),.gain_treble(GAIN_TREBLE));

reg [15:0] mem_in [0: NUM_SAMPLE -1] ;
reg [15:0] mem_gold [0:NUM_SAMPLE -1] ;
integer f_out , i ;
integer count =0 ; 
integer error =0 ; 

`ifdef VCD
initial begin $dumpfile("audio_quality_tb.vcd");
$dumpvars(0, audio_quality_tb); end
`endif
initial  begin
$readmemh(IN_FILE, mem_in);
if(CHECK_GOLDEN) $readmemh(GOLDEN_FILE, mem_gold) ;
f_out = $fopen(OUT_FILE, "w");
if(f_out == 0 ) begin 
$display("Error opening files: %s" , OUT_FILE);
$finish ;
end 
repeat(10) @(posedge clk);
rst <=0 ; 
repeat(5)@(posedge clk);
for(i =0 ;  i< NUM_SAMPLE; i= i+1) begin 
@(posedge clk) ;
x_in <= mem_in[i] ;
in_valid <= 1'b1 ; 
@(posedge clk) ; 
in_valid <= 1'b0 ; 
repeat(CLK_E - 2) @(posedge clk);
end
repeat(CLK_E) @(posedge clk); 
$fclose(f_out);
$display("----------------------");
$display("So mau vao: %0d", NUM_SAMPLE);
$display("So mau ra: %0d" , count);
if(count != NUM_SAMPLE) begin 
$display("Dau ra khac dau vao"); end 
if(CHECK_GOLDEN) begin 
$display("So mau lech: %0d" , error);
if(error == 0 && count == NUM_SAMPLE) begin
$display("PASS");
end else begin $display("FAIL"); end
end
$display("--------------");
$finish ;
end
always@(posedge clk) begin 
if(!rst && out_valid) begin 
$fdisplay(f_out, "%04h", out);
if(CHECK_GOLDEN && count < NUM_SAMPLE) begin
if(out !==  mem_gold[count]) begin 
error = error + 1 ;
if(error <= 10) begin 
$display("Lech n: %0d -- ouput: %4h-- mem_gold: %04h" , count, out, mem_gold[count]);
end
end
end
count = count + 1 ;
end

end


endmodule