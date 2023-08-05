using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Linq;
using Color = System.Drawing.Color;
using Rectangle = System.Drawing.Rectangle;

namespace Chess_Challenge.NEAT_Bot; 

public static class HelperFuncs {
    public static void DrawNetwork(Genome genome, string filename) {
         int width = 2000;
         int height = 2000;
         int radius = 50;
         var bitmap = new Bitmap(width, height);
         var g = Graphics.FromImage(bitmap);

         // Calculate the positions of the nodes in the image
         var positions = CalculatePositions(genome, width, height);

         // Draw the connections
         DrawConnections(g, genome, positions);

         // Draw the nodes
         DrawNodes(g, genome, positions, radius);

         // Save the image
         bitmap.Save(filename, ImageFormat.Png);
     }

     private static Dictionary<Genome.Node, Point> CalculatePositions(Genome genome, int width, int height)
     {
         var positions = new Dictionary<Genome.Node, Point>();
         var nodeDepths = genome.Nodes.Select(node => node.Depth).Distinct().ToList();
         var maxDepth = nodeDepths.Max();
         var depthOffsets = nodeDepths.ToDictionary(depth => depth, depth => depth.GetHashCode() % 2);

         foreach (var depth in nodeDepths)
         {
             var nodesAtDepth = genome.Nodes.Where(node => node.Depth == depth).ToList();
             var verticalSpacing = CalculateVerticalSpacing(height, nodesAtDepth.Count);

             for (var i = 0; i < nodesAtDepth.Count; i++)
             {
                 var node = nodesAtDepth[i];
                 int x = (depth + 1) * (width / (maxDepth + 2)) ;
                 int y = (i + 1) * verticalSpacing + depthOffsets[depth]*50;
                 positions[node] = new Point(x, y);
             }
         }
         return positions;
     }

     private static int CalculateVerticalSpacing(int height, int count)
     {
         return height / (count + 1);
     }

     private static void DrawConnections(Graphics g, Genome genome, Dictionary<Genome.Node, Point> positions)
     {
         // Assume these are the known min and max weights; adjust if needed.
         var minWeight = -1.0;
         var maxWeight = 1.0;

         foreach (var connection in genome.Connections)
         {
             if (!connection.IsEnabled)
             {
                 continue;
             }

             var node1Pos = positions[connection.Nodes.Item1];
             var node2Pos = positions[connection.Nodes.Item2];

             // Calculate depth difference and curvature factor
             var depthDifference = Math.Abs(connection.Nodes.Item1.Depth - connection.Nodes.Item2.Depth);
             var curvatureFactor = depthDifference * 50; // Change this value to adjust curvature

             // Define points for bezier curve
             Point start = node1Pos;
             Point control1 = new Point((node1Pos.X + node2Pos.X) / 2, node1Pos.Y - curvatureFactor);
             Point control2 = new Point((node1Pos.X + node2Pos.X) / 2, node2Pos.Y + curvatureFactor);
             Point end = node2Pos;

             // Calculate line thickness and color based on weight
             float thickness = Math.Abs((float)connection.Weight) * 5; // Change this to adjust line thickness
             float t = (float)((connection.Weight - minWeight) / (maxWeight - minWeight));
             int red = (int)(255 * (1 - t));
             int green = (int)(255 * t);
             red = Math.Max(0, Math.Min(255, red));
             green = Math.Max(0, Math.Min(255, green));
             Color color = Color.FromArgb(red, green, 0); // Interpolate between red and green


             // Create a pen with the calculated thickness and color
             using (Pen pen = new Pen(color, thickness))
             {
                 // Draw bezier curve
                 g.DrawBezier(pen, start, control1, control2, end);
             }

             // Draw the weight of the connection
             var weightPos = new Point((node1Pos.X + node2Pos.X) / 2, (node1Pos.Y + node2Pos.Y) / 2);
             g.DrawString(Math.Round(connection.Weight, 2).ToString(), new System.Drawing.Font("Arial", 16), Brushes.Black, weightPos);
         }
     }


     private static void DrawNodes(Graphics g, Genome genome, Dictionary<Genome.Node, Point> positions, int radius)
     {
         foreach (var node in genome.Nodes)
         {
             var pos = positions[node];
             g.FillEllipse(Brushes.Blue, pos.X - radius / 2, pos.Y - radius / 2, radius, radius);

             // Draw the ID of the node
             var format = new StringFormat() { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center };
             g.DrawString(node.ID.ToString(), new System.Drawing.Font("Arial", 16), Brushes.White, new Rectangle(pos.X - radius / 2, pos.Y - radius / 2, radius, radius), format);
         }
     }

     public static void PrintGenome(Genome genome) {
         Console.WriteLine("Nodes:");
         foreach (Genome.Node node in genome.Nodes) {
             Console.WriteLine($"  ID: {node.ID}, Type: {node.Type}, Depth: {node.Depth}");
         }

         Console.WriteLine("Connections:");
         foreach (Genome.Connection connection in genome.Connections) {
             Genome.Node node1 = connection.Nodes.Item1;
             Genome.Node node2 = connection.Nodes.Item2;

             Console.WriteLine($"  Nodes: {node1.ID}, {node2.ID}, Weight: {connection.Weight}, Enabled: {connection.IsEnabled}, Innovation: {connection.InnovationNumber}");
         }
     }
}