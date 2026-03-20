use std::fmt;
use visioncortex::{Color, CompoundPath, PointF64};

#[derive(Debug, Clone)]
pub struct SvgFile {
    pub paths: Vec<SvgPath>,
    pub width: usize,
    pub height: usize,
    pub path_precision: Option<u32>,
}

#[derive(Debug, Clone)]
pub struct SvgPath {
    pub path: CompoundPath,
    pub color: Color,
    pub stroke_width: Option<f64>,
    pub stroke_color: Option<String>,
}

impl SvgFile {
    pub fn new(width: usize, height: usize, path_precision: Option<u32>) -> Self {
        SvgFile {
            paths: vec![],
            width,
            height,
            path_precision,
        }
    }

    pub fn add_path(&mut self, path: CompoundPath, color: Color, stroke_width: Option<f64>, stroke_color: Option<String>) {
        self.paths.push(SvgPath { 
            path, 
            color, 
            stroke_width, 
            stroke_color 
        })
    }
}

impl fmt::Display for SvgFile {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        writeln!(f, r#"<?xml version="1.0" encoding="UTF-8"?>"#)?;
        writeln!(
            f,
            r#"<!-- Generator: visioncortex VTracer {} -->"#,
            env!("CARGO_PKG_VERSION")
        )?;
        writeln!(
            f,
            r#"<svg version="1.1" xmlns="http://www.w3.org/2000/svg" width="{}" height="{}">"#,
            self.width, self.height
        )?;

        for path in &self.paths {
            path.fmt_with_precision(f, self.path_precision)?;
        }

        writeln!(f, "</svg>")
    }
}

impl fmt::Display for SvgPath {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        self.fmt_with_precision(f, None)
    }
}

impl SvgPath {
    fn fmt_with_precision(&self, f: &mut fmt::Formatter, precision: Option<u32>) -> fmt::Result {
        let (string, offset) = self
            .path
            .to_svg_string(true, PointF64::default(), precision);
        
        // 基础SVG路径属性
        let mut attributes = vec![
            format!("d=\"{}\"", string),
            format!("fill=\"{}\"", self.color.to_hex_string()),
            format!("transform=\"translate({}, {})\"", offset.x, offset.y)
        ];
        
        // 添加轮廓线属性（如果指定）
        if let Some(stroke_width) = self.stroke_width {
            attributes.push(format!("stroke-width=\"{:.1}px\"", stroke_width));
            
            // 如果没有指定轮廓颜色，默认使用黑色
            let stroke_color = self.stroke_color.as_deref().unwrap_or("black");
            attributes.push(format!("stroke=\"{}\"", stroke_color));
        }
        
        writeln!(
            f,
            "<path {} />",
            attributes.join(" ")
        )
    }
}
