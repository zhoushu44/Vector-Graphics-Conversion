use std::fmt;

use resvg::tiny_skia::{LineCap, LineJoin, PathBuilder, PathSegment, Stroke};
use visioncortex::{Color, CompoundPath, CompoundPathElement, PointF64};

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
    pub expand_stroke: bool,
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

    pub fn add_path(
        &mut self,
        path: CompoundPath,
        color: Color,
        stroke_width: Option<f64>,
        stroke_color: Option<String>,
        expand_stroke: bool,
    ) {
        self.paths.push(SvgPath {
            path,
            color,
            stroke_width,
            stroke_color,
            expand_stroke,
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
        let (fill_path, offset) = self
            .path
            .to_svg_string(true, PointF64::default(), precision);

        match (self.stroke_width, self.expand_stroke) {
            (Some(stroke_width), true) if stroke_width > 0.0 => {
                let fill_attributes = vec![
                    format!("d=\"{}\"", fill_path),
                    format!("fill=\"{}\"", self.color.to_hex_string()),
                    format!("transform=\"translate({}, {})\"", offset.x, offset.y),
                ];
                writeln!(f, "<path {} />", fill_attributes.join(" "))?;

                if let Some(expanded_path) = self.expanded_stroke_path(precision) {
                    let stroke_color = self.stroke_color.as_deref().unwrap_or("black");
                    writeln!(
                        f,
                        "<path d=\"{}\" fill=\"{}\" fill-rule=\"nonzero\" />",
                        expanded_path,
                        stroke_color
                    )?;
                }
            }
            (Some(stroke_width), false) if stroke_width > 0.0 => {
                writeln!(
                    f,
                    "<path d=\"{}\" fill=\"{}\" transform=\"translate({}, {})\" stroke-width=\"{:.1}px\" stroke=\"{}\" />",
                    fill_path,
                    self.color.to_hex_string(),
                    offset.x,
                    offset.y,
                    stroke_width,
                    self.stroke_color.as_deref().unwrap_or("black")
                )?;
            }
            _ => {
                let fill_attributes = vec![
                    format!("d=\"{}\"", fill_path),
                    format!("fill=\"{}\"", self.color.to_hex_string()),
                    format!("transform=\"translate({}, {})\"", offset.x, offset.y),
                ];
                writeln!(f, "<path {} />", fill_attributes.join(" "))?;
            }
        }

        Ok(())
    }

    fn expanded_stroke_path(&self, precision: Option<u32>) -> Option<String> {
        let path = compound_path_to_tiny_skia_path(&self.path)?;
        let stroke_width = self.stroke_width? as f32;
        let stroked = path.stroke(
            &Stroke {
                width: stroke_width,
                line_cap: LineCap::Round,
                line_join: LineJoin::Round,
                ..Stroke::default()
            },
            1.0,
        )?;

        Some(tiny_skia_path_to_svg_string(&stroked, precision))
    }
}

fn compound_path_to_tiny_skia_path(path: &CompoundPath) -> Option<resvg::tiny_skia::Path> {
    let mut builder = PathBuilder::new();

    for element in path.iter() {
        match element {
            CompoundPathElement::PathI32(path) => {
                let closed = path.to_closed();
                if closed.path.is_empty() {
                    continue;
                }

                builder.move_to(closed.path[0].x as f32, closed.path[0].y as f32);
                for point in closed.path.iter().skip(1).take(closed.path.len().saturating_sub(2)) {
                    builder.line_to(point.x as f32, point.y as f32);
                }
                builder.close();
            }
            CompoundPathElement::PathF64(path) => {
                let closed = path.to_closed();
                if closed.path.is_empty() {
                    continue;
                }

                builder.move_to(closed.path[0].x as f32, closed.path[0].y as f32);
                for point in closed.path.iter().skip(1).take(closed.path.len().saturating_sub(2)) {
                    builder.line_to(point.x as f32, point.y as f32);
                }
                builder.close();
            }
            CompoundPathElement::Spline(path) => {
                if path.is_empty() {
                    continue;
                }

                builder.move_to(path.points[0].x as f32, path.points[0].y as f32);
                let mut i = 1;
                while i + 2 < path.points.len() {
                    builder.cubic_to(
                        path.points[i].x as f32,
                        path.points[i].y as f32,
                        path.points[i + 1].x as f32,
                        path.points[i + 1].y as f32,
                        path.points[i + 2].x as f32,
                        path.points[i + 2].y as f32,
                    );
                    i += 3;
                }
                builder.close();
            }
        }
    }

    builder.finish()
}

fn tiny_skia_path_to_svg_string(path: &resvg::tiny_skia::Path, precision: Option<u32>) -> String {
    let mut result = String::new();

    for segment in path.segments() {
        match segment {
            PathSegment::MoveTo(point) => {
                result.push_str(&format!(
                    "M{} {} ",
                    format_number(point.x as f64, precision),
                    format_number(point.y as f64, precision)
                ));
            }
            PathSegment::LineTo(point) => {
                result.push_str(&format!(
                    "L{} {} ",
                    format_number(point.x as f64, precision),
                    format_number(point.y as f64, precision)
                ));
            }
            PathSegment::QuadTo(control, point) => {
                result.push_str(&format!(
                    "Q{} {} {} {} ",
                    format_number(control.x as f64, precision),
                    format_number(control.y as f64, precision),
                    format_number(point.x as f64, precision),
                    format_number(point.y as f64, precision)
                ));
            }
            PathSegment::CubicTo(control1, control2, point) => {
                result.push_str(&format!(
                    "C{} {} {} {} {} {} ",
                    format_number(control1.x as f64, precision),
                    format_number(control1.y as f64, precision),
                    format_number(control2.x as f64, precision),
                    format_number(control2.y as f64, precision),
                    format_number(point.x as f64, precision),
                    format_number(point.y as f64, precision)
                ));
            }
            PathSegment::Close => result.push_str("Z "),
        }
    }

    result
}

fn format_number(num: f64, precision: Option<u32>) -> String {
    match precision {
        None => format!("{}", num),
        Some(0) => format!("{:.0}", num),
        Some(p) => {
            let mut string = format!("{:.1$}", num, p as usize);
            string = string.trim_end_matches('0').trim_end_matches('.').to_owned();
            string
        }
    }
}
